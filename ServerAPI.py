import uvicorn
from fastapi import Depends, FastAPI, Body, Response, HTTPException
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from lib.server.controller.OrderController import OrderController
from lib.server.model.EglemAPIOrderModel import OrderResponse
from lib.server.model.ResponseHttpModel import ResponseHttp
from typing import List, Dict
from lib.auth.Auth import Auth
import logging
from decouple import config

# Initialize Logger
logging.basicConfig(filename=config('LOGGING_FILE'), level=config('LOGGING_LEVEL'))

# Initialize the FastAPI
app = FastAPI()

@app.get("/order")
def getOrders(token: str  = Depends(Auth.verify_token)):
    orderList = OrderController.getOrders()
    return orderList

@app.put("/order/status")
def changeOrderStatus(token: str = Depends(Auth.verify_token), orders_and_status: List[Dict[str, str]] = Body(None, alias=None, title=None, description="List of object contains order_id and order_status")):
    response = OrderController.changeOrderStatus(orders_and_status, token)
    return JSONResponse(status_code=response.get('status_code'), content=response.get('content'))

@app.post("/shipment/tracking")
def addTracking(token: str = Depends(Auth.verify_token), id_ordine: str = Body(None, alias=None, title=None, description="id_order"), codice_tracking: str = Body(None, alias=None, title=None, description="codice_tracking to add to the shipment")):
    response = OrderController.addTracking(id_ordine, codice_tracking, token)
    return JSONResponse(status_code=response.get('status_code'), content=response.get('content'))

@app.post("/shipment/trackings")
def addTrackings(token: str = Depends(Auth.verify_token), data: List[Dict[str, str]] = Body(None, alias=None, title=None, description="List of object contains order_id and codice_tracking")):
    response = OrderController.addTrackings(data, token)
    return JSONResponse(status_code=response.get('status_code'), content=response.get('content'))



if __name__ == "__main__":
    uvicorn.run(
        "ServerAPI:app",
        host="0.0.0.0",
        port=8080,
        log_level="debug",
        reload=True,
    )


