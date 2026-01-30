import pyodbc
import logging
from typing import List, Dict, Any

class DBClient:
    def __init__(self, dsn: str, user: str, password: str):
        self.dsn = dsn
        self.user = user
        self.password = password
        self.connection_string = f"DSN={dsn};UID={user};PWD={password}"

    def get_albaran_details(self, albaran_numbers: List[str]) -> List[Dict[str, Any]]:
        """
        Queries AS400 for details of the given albaran numbers.
        Returns a list of dictionaries.
        """
        if not albaran_numbers:
            return []

        # Sanitize inputs (ensure they are strings/numbers)
        # The albaran numbers from PDF filename might need casting or trimming?
        # Assuming they match EMCNUM or similar field. 
        # Based on user QRY, T01.EMCNUM seems to be the join key.
        
        # Prepare placeholders for IN clause
        placeholders = ",".join("?" for _ in albaran_numbers)
        
        # IMPORTANT: The user provided QRY code has hardcoded library names (LIB001, BIESTADI, "$$LIBFAL").
        # I will use them as is, but this might need adjustment if they are variables.
        # Combined SQL from QRY1 & QRY2 logic.
        
        # QRY2 main logic joined with finding the albaranes.
        # We need to filter T02.EMCDOC (Albaran) or T02.EMCNUM (Num Int)?
        # User said: "lista de los números de albaranes (el nombre de los pdf sin la extensión...)"
        # And QRY1 says: `INNER JOIN LISTA_ALBARANES L ON T01.EMCNUM = L.NUM_ALBARAN`
        # So the filename -> EMCNUM.
        
        sql_query = f"""
        SELECT 
            T01.HVPROG AS cod_barras,
            T01.HVFELA AS flag,
            T02.EMCALM AS alm,
            T02.EMCNUM AS num_int,
            T02.EMCFEE AS fecha,
            T02.EMCMAY AS cuenta_mayor,
            T02.EMCCTA AS prov_codigo,
            T02.EMCDIV AS division,
            T02.EMCSER AS serie,
            T02.EMCDOC AS albaran,
            T03.PDDESC AS proveedor_desc
        FROM "$$LIBFAL".DRVAA00K AS T01
        LEFT JOIN LIB001.ENTMEC AS T02 
            ON T01.HVKEY1 = T02.EMCALM 
            AND T01.HVKEY2 = T02.EMCNUM
        -- We join T02 (ENTMEC + FECA28 logic from QRY1) effectively here
        -- Note: QRY2 used a View/Table BIESTADI.ENTALFA28 which was QRY1.
        -- QRY1 was: ENTMEC + FECA28.
        -- To keep it simple and one query, I will rely on T02 (ENTMEC) and if FECA28 is needed for fields not in ENTMEC, I'd add it.
        -- But QRY2 selects from T02.* where T02 is BIESTADI.ENTALFA28.
        -- BIESTADI.ENTALFA28 had: NUMENT, CODALMA, T01.* (ENTMEC).
        -- So T02 in QRY2 is basically ENTMEC.
        
        -- Join with Provider Master
        LEFT JOIN LIB001.PRODIV AS T03
            ON T02.EMCMAY = T03.PDMAYO
            AND T02.EMCCTA = T03.PDCTAA
            AND T02.EMCDIV = T03.PDDIVI
            
        WHERE 
            T01.HVPROG IN ({placeholders})
            
        ORDER BY 
            T02.EMCALM ASC,
            T02.EMCNUM ASC
        """
        
        results = []
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute(sql_query, albaran_numbers)
                
                columns = [column[0] for column in cursor.description]
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                    
        except Exception as e:
            logging.error(f"Database error: {e}")
            # If development/dry_run without DB, return empty or mock? 
            # For now just log and re-raise or return empty.
            raise e
            
        return results
