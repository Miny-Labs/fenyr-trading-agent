"""
WEEX API Client for Fenyr Trading Agent
Handles all communication with WEEX Exchange API
"""

import time
import hmac
import hashlib
import base64
import requests
import json
from typing import Optional, Dict, Any, List


class WeexClient:
    """WEEX Exchange API Client"""
    
    def __init__(self, api_key: str, secret_key: str, passphrase: str, base_url: str):
        self.api_key = api_key
        self.secret_key = secret_key
        self.passphrase = passphrase
        self.base_url = base_url
        self.session = requests.Session()
    
    def _get_timestamp(self) -> str:
        return str(int(time.time() * 1000))
    
    def _sign(self, timestamp: str, method: str, path: str, body: str = "") -> str:
        message = timestamp + method.upper() + path + body
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256
        ).digest()
        return base64.b64encode(signature).decode()
    
    def _headers(self, timestamp: str, signature: str) -> Dict[str, str]:
        return {
            "ACCESS-KEY": self.api_key,
            "ACCESS-SIGN": signature,
            "ACCESS-TIMESTAMP": timestamp,
            "ACCESS-PASSPHRASE": self.passphrase,
            "Content-Type": "application/json",
            "locale": "en-US"
        }
    
    def _get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """Make authenticated GET request"""
        qs = ""
        if params:
            qs = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        
        timestamp = self._get_timestamp()
        signature = self._sign(timestamp, "GET", path + qs)
        headers = self._headers(timestamp, signature)
        
        url = self.base_url + path + qs
        response = self.session.get(url, headers=headers)
        return response.json()
    
    def _post(self, path: str, body: Dict) -> Dict:
        """Make authenticated POST request"""
        body_str = json.dumps(body)
        timestamp = self._get_timestamp()
        signature = self._sign(timestamp, "POST", path, body_str)
        headers = self._headers(timestamp, signature)
        
        url = self.base_url + path
        response = self.session.post(url, headers=headers, data=body_str)
        return response.json()
    
    def _public_get(self, path: str, params: Optional[Dict] = None) -> Dict:
        """Make public GET request (no auth)"""
        qs = ""
        if params:
            qs = "?" + "&".join(f"{k}={v}" for k, v in params.items())
        url = self.base_url + path + qs
        response = self.session.get(url)
        return response.json()
    
    # ==================== MARKET DATA ====================
    
    def get_ticker(self, symbol: str) -> Dict:
        """Get current ticker for symbol"""
        return self._public_get("/capi/v2/market/ticker", {"symbol": symbol})
    
    def get_depth(self, symbol: str, depth_type: str = "step0") -> Dict:
        """Get orderbook depth"""
        return self._public_get("/capi/v2/market/depth", {"symbol": symbol, "type": depth_type})
    
    def get_candles(self, symbol: str, granularity: str = "1h", limit: int = 100) -> List:
        """Get candlestick/kline data"""
        return self._public_get("/capi/v2/market/candles", {
            "symbol": symbol,
            "granularity": granularity,
            "limit": limit
        })
    
    def get_funding_rate(self, symbol: str) -> Dict:
        """Get current funding rate"""
        return self._public_get("/capi/v2/market/fundingRate", {"symbol": symbol})
    
    def get_contracts(self, symbol: Optional[str] = None) -> List:
        """Get contract information"""
        params = {"symbol": symbol} if symbol else {}
        return self._public_get("/capi/v2/market/contracts", params)
    
    # ==================== ACCOUNT ====================
    
    def get_assets(self) -> List:
        """Get account assets/balance"""
        return self._get("/capi/v2/account/assets")
    
    def get_positions(self) -> List:
        """Get all positions"""
        return self._get("/capi/v2/account/position/allPosition")
    
    def get_position(self, symbol: str) -> Dict:
        """Get single position"""
        return self._get("/capi/v2/account/position/singlePosition", {"symbol": symbol})
    
    def set_leverage(self, symbol: str, leverage: int) -> Dict:
        """Set leverage for symbol"""
        return self._post("/capi/v2/account/leverage", {
            "symbol": symbol,
            "marginMode": 1,
            "longLeverage": str(leverage),
            "shortLeverage": str(leverage)
        })
    
    # ==================== ORDERS ====================
    
    def place_order(
        self,
        symbol: str,
        size: str,
        side: int,  # 1=open_long, 2=close_short, 3=open_short, 4=close_long
        order_type: int = 0,  # 0=limit, 1=market
        price: Optional[str] = None,
        client_oid: Optional[str] = None
    ) -> Dict:
        """Place a futures order"""
        body = {
            "symbol": symbol,
            "size": size,
            "type": str(side),
            "order_type": str(order_type),
            "match_price": "1" if order_type == 1 else "0"
        }
        if price and order_type == 0:
            body["price"] = price
        if client_oid:
            body["client_oid"] = client_oid
        else:
            body["client_oid"] = str(int(time.time() * 1000))
        
        return self._post("/capi/v2/order/placeOrder", body)
    
    def cancel_order(self, symbol: str, order_id: str) -> Dict:
        """Cancel an order"""
        return self._post("/capi/v2/order/cancelOrder", {
            "symbol": symbol,
            "orderId": order_id
        })
    
    def get_order_history(self, symbol: str, page_size: int = 20) -> List:
        """Get order history"""
        return self._get("/capi/v2/order/history", {
            "symbol": symbol,
            "pageSize": page_size
        })
    
    def get_fills(self, symbol: str) -> List:
        """Get trade fills"""
        return self._get("/capi/v2/order/fills", {"symbol": symbol})
    
    # ==================== AI LOG ====================
    
    def upload_ai_log(
        self,
        stage: str,
        model: str,
        input_data: Dict,
        output_data: Dict,
        explanation: str,
        order_id: Optional[int] = None
    ) -> Dict:
        """Upload AI log for competition compliance"""
        body = {
            "stage": stage,
            "model": model,
            "input": input_data,
            "output": output_data,
            "explanation": explanation[:1000]  # Max 1000 chars
        }
        if order_id:
            body["orderId"] = order_id
        
        return self._post("/capi/v2/order/uploadAiLog", body)


# Factory function
def create_client(api_key: str, secret_key: str, passphrase: str, base_url: str) -> WeexClient:
    """Create a WEEX client instance"""
    return WeexClient(api_key, secret_key, passphrase, base_url)
