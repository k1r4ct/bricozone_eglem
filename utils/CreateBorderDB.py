from lib.helper.SQLHelper import SQLHelper

class CreateBorderDB:

    #create the border db to store product history 
    @staticmethod
    def createBorderDB(options={"connection":None,"close":True}):
        try:
            connection = options["connection"] if options["connection"] else SQLHelper.getConnection()
            cursor = connection.cursor()
            cursor.execute("CREATE DATABASE eglem CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci")
            sqlCreateTable = "CREATE TABLE eglem.product_history (id int NOT NULL AUTO_INCREMENT, sku varchar(100), id_eglem varchar(100), quantity varchar(11), price float(7,2), timestamp datetime NOT NULL DEFAULT CURRENT_TIMESTAMP, status varchar(100), jobuuid varchar(100), PRIMARY KEY (id));"
            cursor.execute(sqlCreateTable)
            connection.commit()

        except Exception as ex:
            print("An exception has been thrown during the creation of the border database and the product_history table: ", str(ex))

        finally:
            if options["close"]:
                SQLHelper.connectionClose(connection)

CreateBorderDB.createBorderDB()


