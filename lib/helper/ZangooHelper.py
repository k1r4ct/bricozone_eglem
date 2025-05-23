import mysql.connector
import logging
from lib.helper.SQLHelper import SQLHelper
from lib.helper.CatalogImporterConfigHelper import config

class ZangooDbHelper(SQLHelper):
    """
    Helper to manage operations on the Zangoo database
    """

    @staticmethod
    def getConnection():
        """Get a connection to the Zangoo database"""
        return SQLHelper.getConnection(
            config('ZANGOO_DEV_DB_HOST', default='127.0.0.1'), 
            config('ZANGOO_DEV_DB_PORT', default=3307, cast=int), 
            config('ZANGOO_DEV_DB_DATABASE'), 
            config('ZANGOO_DEV_DB_USER', default='root'), 
            config('ZANGOO_DEV_DB_PASSWORD', default='password')
        )

    @staticmethod
    def connectionClose(connection):
        """Close database connection"""
        return SQLHelper.connectionClose(connection)

    @staticmethod
    def getCategoryPaths(options={"connection": None, "close": True}):
        """
        Retrieve all unique category paths from Zangoo
        
        Returns:
            List[str]: List of category paths
        """
        try:
            connection = options["connection"] if options["connection"] else ZangooDbHelper.getConnection()
            cursor = connection.cursor()
            
            # Query provided by the user to retrieve category paths
            select_query = """
                SELECT CONCAT_WS('/',
                    cat0.nome,
                    cat1.nome,
                    cat2.nome,
                    cat3.nome) AS categories
                FROM categorie c
                LEFT JOIN categorie cat3 ON cat3.id = c.id
                LEFT JOIN categorie cat2 ON cat2.id = cat3.id_parent
                LEFT JOIN categorie cat1 ON cat1.id = cat2.id_parent
                LEFT JOIN categorie cat0 ON cat0.id = cat1.id_parent
                GROUP BY categories
                HAVING categories IS NOT NULL AND categories != ''
                ORDER BY categories
            """
            
            cursor.execute(select_query)
            results = cursor.fetchall()
            
            # Extract only the paths from tuples
            category_paths = []
            for row in results:
                path = row[0]
                if path and path.strip():
                    # Clean the path by removing multiple slashes and trailing slash
                    clean_path = '/'.join([segment.strip() for segment in path.split('/') if segment.strip()])
                    if clean_path:
                        category_paths.append(clean_path)
            
            logging.info(f"Retrieved {len(category_paths)} category paths from Zangoo")
            return category_paths
            
        except Exception as ex:
            logging.error(f"Error retrieving category paths: {str(ex)}")
            return []
        
        finally:
            if options["close"]:
                ZangooDbHelper.connectionClose(connection)

    @staticmethod
    def testConnection():
        """
        Test the connection to Zangoo database
        
        Returns:
            bool: True if the connection was successful
        """
        try:
            connection = ZangooDbHelper.getConnection()
            if connection and connection.is_connected():
                cursor = connection.cursor()
                cursor.execute("SELECT COUNT(*) FROM categorie")
                count = cursor.fetchone()[0]
                ZangooDbHelper.connectionClose(connection)
                logging.info(f"Connection to Zangoo successful. Found {count} categories in the table.")
                return True
        except Exception as ex:
            logging.error(f"Error connecting to Zangoo: {str(ex)}")
            return False
        
        return False

    @staticmethod
    def getCategoriesCount(options={"connection": None, "close": True}):
        """
        Get the total count of categories in the database
        
        Returns:
            int: Number of categories
        """
        try:
            connection = options["connection"] if options["connection"] else ZangooDbHelper.getConnection()
            cursor = connection.cursor()
            
            cursor.execute("SELECT COUNT(*) FROM categorie")
            count = cursor.fetchone()[0]
            
            return count
            
        except Exception as ex:
            logging.error(f"Error counting categories: {str(ex)}")
            return 0
        
        finally:
            if options["close"]:
                ZangooDbHelper.connectionClose(connection)