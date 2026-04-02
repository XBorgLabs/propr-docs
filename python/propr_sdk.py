"""
Propr Python SDK
Official client for the Propr trading API.

Usage:
    from propr_sdk import ProprClient

    client = ProprClient()
    client.setup()
    print(client.get_positions())
"""

import os
from decimal import Decimal
from typing import Any, Optional
from ulid import ULID

import requests
from dotenv import load_dotenv

load_dotenv()

__version__ = "0.1.0"


class ProprAPIError(Exception):
    """Raised when the Propr API returns an error response."""

    def __init__(self, status_code: int, code: int | None, message: str, response: requests.Response):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.response = response
        super().__init__(f"[{status_code}] {code}: {message}")


class ProprClient:
    """
    Propr trading API client.

    Args:
        api_key: Your API key (pk_live_...). Falls back to PROPR_API_KEY env var.
        base_url: API base URL. Falls back to PROPR_API_URL env var or production default.
        timeout: Request timeout in seconds. Default 30.
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        timeout: int = 30,
    ):
        self.api_key = api_key or os.getenv("PROPR_API_KEY")
        self.base_url = (
            base_url
            or os.getenv("PROPR_API_URL")
            or "https://api.propr.xyz/v1"
        )
        self.timeout = timeout
        self.account_id: str | None = None
        self._session = requests.Session()
        self._session.headers.update({
            "Content-Type": "application/json",
        })
        if self.api_key:
            self._session.headers["X-API-Key"] = self.api_key

        if not self.api_key:
            raise ValueError(
                "API key required. Set PROPR_API_KEY env var or pass api_key parameter.\n"
                "Get your key at https://app.propr.xyz/settings"
            )

    # ── Internal ──

    def _request(
        self,
        method: str,
        path: str,
        params: dict | None = None,
        json: dict | None = None,
    ) -> requests.Response:
        """Make an API request and raise on error."""
        url = f"{self.base_url}{path}"
        response = self._session.request(
            method, url, params=params, json=json, timeout=self.timeout
        )

        if response.status_code >= 400:
            try:
                body = response.json()
                code = body.get("code")
                message = body.get("message", "unknown_error")
            except Exception:
                code = None
                message = response.text or "unknown_error"
            raise ProprAPIError(response.status_code, code, message, response)

        return response

    def _get(self, path: str, params: dict | None = None) -> Any:
        return self._request("GET", path, params=params).json()

    def _post(self, path: str, json: dict | None = None) -> Any:
        return self._request("POST", path, json=json).json()

    def _put(self, path: str, json: dict | None = None) -> Any:
        return self._request("PUT", path, json=json).json()

    def _account_path(self, suffix: str) -> str:
        """Build /accounts/{accountId}/... path. Raises if account_id not set."""
        if not self.account_id:
            raise ValueError(
                "account_id not set. Call client.setup() first or set client.account_id manually."
            )
        return f"/accounts/{self.account_id}{suffix}"

    # ── Setup ──

    def setup(self, account_id: str | None = None) -> str:
        """
        Initialize the client with an account ID.

        If account_id is provided, uses that directly. Otherwise, fetches
        the first active challenge attempt and extracts its accountId.

        Returns:
            The account ID being used.
        """
        if account_id:
            self.account_id = account_id
            return self.account_id

        attempts = self.get_challenge_attempts(status="active")
        if not attempts:
            raise Exception(
                "No active challenge found. Purchase a challenge at "
                "https://app.propr.xyz/dashboard first."
            )
        self.account_id = attempts[0]["accountId"]
        return self.account_id

    # ── Health ──

    def health(self) -> dict:
        """
        Check API health.

        Returns:
            {"status": "OK"}
        """
        return self._get("/health")

    def health_services(self) -> dict:
        """
        Check backend service health.

        Returns:
            {"core": "OK" | "ERROR"}
        """
        return self._get("/health/services")

    # ── User ──

    def get_user(self) -> dict:
        """
        Get the current authenticated user's profile.

        Returns:
            User profile dict with userId, email, name, etc.
        """
        return self._get("/users/me")

    # ── Challenges ──

    def get_challenges(
        self,
        challenge_id: str | None = None,
        product_id: str | None = None,
        currency: str | None = None,
        exchange: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List available trading challenges. No authentication required.

        Args:
            challenge_id: Filter by challenge ID.
            product_id: Filter by product ID.
            currency: Filter by currency (USDC, USD, EUR).
            exchange: Filter by exchange (hyperliquid).
            limit: Results per page (default 20).
            offset: Pagination offset.

        Returns:
            List of challenge dicts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if challenge_id:
            params["challengeId"] = challenge_id
        if product_id:
            params["productId"] = product_id
        if currency:
            params["currency"] = currency
        if exchange:
            params["exchange"] = exchange

        return self._get("/challenges", params=params).get("data", [])

    # ── Challenge Attempts ──

    def get_challenge_attempts(
        self,
        attempt_id: str | None = None,
        challenge_id: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List your challenge attempts.

        Args:
            attempt_id: Filter by attempt ID.
            challenge_id: Filter by challenge ID.
            status: Filter by status (active, passed, failed).
            limit: Results per page.
            offset: Pagination offset.

        Returns:
            List of attempt dicts with accountId, status, profit, etc.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if attempt_id:
            params["attemptId"] = attempt_id
        if challenge_id:
            params["challengeId"] = challenge_id
        if status:
            params["status"] = status

        return self._get("/challenge-attempts", params=params).get("data", [])

    def get_challenge_attempt(self, attempt_id: str) -> dict:
        """
        Get a specific challenge attempt.

        Args:
            attempt_id: The attempt ID.

        Returns:
            Attempt dict.
        """
        return self._get(f"/challenge-attempts/{attempt_id}")

    # ── Orders ──

    def get_orders(
        self,
        order_id: str | None = None,
        trade_id: str | None = None,
        position_id: str | None = None,
        base: str | None = None,
        quote: str | None = None,
        side: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List orders for the account.

        Args:
            order_id: Filter by order ID.
            trade_id: Filter by trade ID.
            position_id: Filter by position ID.
            base: Filter by base asset (BTC, ETH, etc.).
            quote: Filter by quote asset (USDC).
            side: Filter by side (buy, sell).
            status: Filter by status (open, filled, cancelled, etc.).
            limit: Results per page.
            offset: Pagination offset.

        Returns:
            List of order dicts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if order_id:
            params["orderId"] = order_id
        if trade_id:
            params["tradeId"] = trade_id
        if position_id:
            params["positionId"] = position_id
        if base:
            params["base"] = base
        if quote:
            params["quote"] = quote
        if side:
            params["side"] = side
        if status:
            params["status"] = status

        return self._get(self._account_path("/orders"), params=params).get("data", [])

    def create_order(
        self,
        side: str,
        position_side: str,
        order_type: str,
        asset: str,
        base: str,
        quote: str,
        quantity: str,
        price: str | None = None,
        trigger_price: str | None = None,
        time_in_force: str | None = None,
        reduce_only: bool = False,
        close_position: bool = False,
    ) -> list[dict]:
        """
        Place a single order.

        Args:
            side: Order side ("buy" or "sell").
            position_side: Position side ("long" or "short").
            order_type: One of "market", "limit", "stop_market", "stop_limit",
                        "take_profit_market", "take_profit_limit".
            asset: Trading pair (e.g. "BTC/USDC").
            base: Base asset (e.g. "BTC").
            quote: Quote asset (e.g. "USDC").
            quantity: Order quantity as string.
            price: Limit price as string (required for limit orders).
            trigger_price: Trigger price for stop/TP orders.
            time_in_force: "GTC" (default), "IOC", "FOK", "GTX".
                           Defaults to "IOC" for market orders, "GTC" for others.
            reduce_only: If True, order can only reduce existing position.
            close_position: If True, closes entire position.

        Returns:
            List of created order dicts.
        """
        if not time_in_force:
            time_in_force = "IOC" if order_type == "market" else "GTC"

        order: dict[str, Any] = {
            "accountId": self.account_id,
            "intentId": str(ULID()),
            "exchange": "hyperliquid",
            "type": order_type,
            "side": side,
            "positionSide": position_side,
            "productType": "perp",
            "timeInForce": time_in_force,
            "asset": asset,
            "base": base,
            "quote": quote,
            "quantity": str(quantity),
            "reduceOnly": reduce_only,
            "closePosition": close_position,
        }
        if price is not None:
            order["price"] = str(price)
        if trigger_price is not None:
            order["triggerPrice"] = str(trigger_price)

        return self._post(
            self._account_path("/orders"), json={"orders": [order]}
        ).get("data", [])

    def create_orders(self, orders: list[dict]) -> list[dict]:
        """
        Place multiple orders in a batch.

        Each order dict should contain all required fields. If intentId is missing,
        one is generated automatically.

        Args:
            orders: List of order dicts.

        Returns:
            List of created order dicts.
        """
        for order in orders:
            if "intentId" not in order:
                order["intentId"] = str(ULID())
            if "accountId" not in order:
                order["accountId"] = self.account_id

        return self._post(
            self._account_path("/orders"), json={"orders": orders}
        ).get("data", [])

    def cancel_order(self, order_id: str) -> dict | None:
        """
        Cancel an open order.

        Args:
            order_id: The order ID to cancel.

        Returns:
            Cancelled order dict, or None if already filled/cancelled.
        """
        try:
            return self._post(self._account_path(f"/orders/{order_id}/cancel"))
        except ProprAPIError as e:
            if e.status_code == 400:
                return None  # Already filled or cancelled
            raise

    def cancel_all_orders(self, base: str | None = None) -> list[dict]:
        """
        Cancel all open orders, optionally filtered by base asset.

        Args:
            base: Only cancel orders for this base asset (e.g. "BTC").

        Returns:
            List of cancelled order dicts.
        """
        params: dict[str, Any] = {"status": "open"}
        if base:
            params["base"] = base

        open_orders = self._get(self._account_path("/orders"), params=params).get("data", [])
        cancelled = []
        for order in open_orders:
            result = self.cancel_order(order["orderId"])
            if result:
                cancelled.append(result)
        return cancelled

    # ── Positions ──

    def get_positions(
        self,
        position_id: str | None = None,
        asset: str | None = None,
        base: str | None = None,
        quote: str | None = None,
        position_side: str | None = None,
        status: str | None = None,
        limit: int = 20,
        offset: int = 0,
        exclude_zero: bool = True,
    ) -> list[dict]:
        """
        List positions for the account.

        Args:
            position_id: Filter by position ID.
            asset: Filter by asset pair (e.g. "BTC/USDC").
            base: Filter by base asset (e.g. "BTC").
            quote: Filter by quote asset (e.g. "USDC").
            position_side: Filter by side ("long" or "short").
            status: Filter by status ("open", "closed", "liquidated").
            limit: Results per page.
            offset: Pagination offset.
            exclude_zero: If True (default), filters out zero-quantity positions.

        Returns:
            List of position dicts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if position_id:
            params["positionId"] = position_id
        if asset:
            params["asset"] = asset
        if base:
            params["base"] = base
        if quote:
            params["quote"] = quote
        if position_side:
            params["positionSide"] = position_side
        if status:
            params["status"] = status

        positions = self._get(self._account_path("/positions"), params=params).get("data", [])

        if exclude_zero:
            positions = [p for p in positions if Decimal(p.get("quantity", "0")) > 0]

        return positions

    def get_open_positions(self, base: str | None = None) -> list[dict]:
        """
        Convenience method: get all open positions with non-zero quantity.

        Args:
            base: Filter by base asset (e.g. "BTC").

        Returns:
            List of open position dicts.
        """
        return self.get_positions(base=base, status="open", exclude_zero=True)

    # ── Trades ──

    def get_trades(
        self,
        trade_id: str | None = None,
        position_id: str | None = None,
        order_id: str | None = None,
        base: str | None = None,
        quote: str | None = None,
        side: str | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        """
        List trade executions for the account.

        Args:
            trade_id: Filter by trade ID.
            position_id: Filter by position ID.
            order_id: Filter by order ID.
            base: Filter by base asset.
            quote: Filter by quote asset.
            side: Filter by side (buy, sell).
            limit: Results per page.
            offset: Pagination offset.

        Returns:
            List of trade dicts.
        """
        params: dict[str, Any] = {"limit": limit, "offset": offset}
        if trade_id:
            params["tradeId"] = trade_id
        if position_id:
            params["positionId"] = position_id
        if order_id:
            params["orderId"] = order_id
        if base:
            params["base"] = base
        if quote:
            params["quote"] = quote
        if side:
            params["side"] = side

        return self._get(self._account_path("/trades"), params=params).get("data", [])

    # ── Margin Configuration ──

    def get_margin_config(self, asset: str) -> dict:
        """
        Get margin configuration for a specific asset.

        Args:
            asset: Base asset (e.g. "BTC", "ETH").

        Returns:
            Margin config dict with configId, leverage, marginMode, etc.
        """
        return self._get(self._account_path(f"/margin-config/{asset}"))

    def update_margin_config(
        self,
        config_id: str,
        asset: str,
        leverage: int,
        margin_mode: str = "cross",
    ) -> dict:
        """
        Update margin configuration for an asset.

        Args:
            config_id: The configId from get_margin_config().
            asset: Base asset (e.g. "BTC").
            leverage: Leverage multiplier (check leverage limits first).
            margin_mode: "cross" or "isolated".

        Returns:
            Updated margin config dict.
        """
        return self._put(
            self._account_path(f"/margin-config/{config_id}"),
            json={
                "exchange": "hyperliquid",
                "asset": asset,
                "marginMode": margin_mode,
                "leverage": leverage,
            },
        )

    # ── Leverage Limits ──

    def get_leverage_limits(self) -> dict:
        """
        Get effective leverage limits for all assets. No auth required.

        Returns:
            {"defaultMax": 2, "overrides": {"BTC": 5, "ETH": 5}}
        """
        return self._get("/leverage-limits/effective")

    def max_leverage(self, asset: str) -> int:
        """
        Get the maximum allowed leverage for a specific asset.

        Args:
            asset: Base asset (e.g. "BTC", "SOL").

        Returns:
            Maximum leverage as integer.
        """
        limits = self.get_leverage_limits()
        return limits.get("overrides", {}).get(asset, limits.get("defaultMax", 2))

    # ── Convenience Methods ──

    def market_buy(
        self,
        base: str,
        quantity: str,
        quote: str = "USDC",
    ) -> list[dict]:
        """
        Place a market buy (long) order.

        Args:
            base: Base asset (e.g. "BTC").
            quantity: Order quantity.
            quote: Quote asset (default "USDC").

        Returns:
            List of created order dicts.
        """
        return self.create_order(
            side="buy",
            position_side="long",
            order_type="market",
            asset=f"{base}/{quote}",
            base=base,
            quote=quote,
            quantity=quantity,
        )

    def market_sell(
        self,
        base: str,
        quantity: str,
        quote: str = "USDC",
        reduce_only: bool = True,
    ) -> list[dict]:
        """
        Place a market sell (close long) order.

        Args:
            base: Base asset (e.g. "BTC").
            quantity: Order quantity.
            quote: Quote asset (default "USDC").
            reduce_only: Safety flag (default True).

        Returns:
            List of created order dicts.
        """
        return self.create_order(
            side="sell",
            position_side="long",
            order_type="market",
            asset=f"{base}/{quote}",
            base=base,
            quote=quote,
            quantity=quantity,
            reduce_only=reduce_only,
        )

    def limit_buy(
        self,
        base: str,
        quantity: str,
        price: str,
        quote: str = "USDC",
    ) -> list[dict]:
        """
        Place a limit buy (long) order.

        Args:
            base: Base asset (e.g. "BTC").
            quantity: Order quantity.
            price: Limit price.
            quote: Quote asset (default "USDC").

        Returns:
            List of created order dicts.
        """
        return self.create_order(
            side="buy",
            position_side="long",
            order_type="limit",
            asset=f"{base}/{quote}",
            base=base,
            quote=quote,
            quantity=quantity,
            price=price,
        )

    def limit_sell(
        self,
        base: str,
        quantity: str,
        price: str,
        quote: str = "USDC",
        reduce_only: bool = True,
    ) -> list[dict]:
        """
        Place a limit sell (close long) order.

        Args:
            base: Base asset (e.g. "BTC").
            quantity: Order quantity.
            price: Limit price.
            quote: Quote asset (default "USDC").
            reduce_only: Safety flag (default True).

        Returns:
            List of created order dicts.
        """
        return self.create_order(
            side="sell",
            position_side="long",
            order_type="limit",
            asset=f"{base}/{quote}",
            base=base,
            quote=quote,
            quantity=quantity,
            price=price,
            reduce_only=reduce_only,
        )

    def close_position(self, base: str, quote: str = "USDC") -> list[dict]:
        """
        Close an entire position on an asset.

        Detects position side automatically and places a market close order.

        Args:
            base: Base asset (e.g. "BTC").
            quote: Quote asset (default "USDC").

        Returns:
            List of created order dicts, or empty if no position found.
        """
        positions = self.get_open_positions(base=base)
        if not positions:
            return []

        pos = positions[0]
        close_side = "sell" if pos["positionSide"] == "long" else "buy"

        return self.create_order(
            side=close_side,
            position_side=pos["positionSide"],
            order_type="market",
            asset=f"{base}/{quote}",
            base=base,
            quote=quote,
            quantity=pos["quantity"],
            reduce_only=True,
            close_position=True,
        )

    def set_leverage(self, asset: str, leverage: int, margin_mode: str = "cross") -> dict:
        """
        Set leverage for an asset (creates or updates margin config).

        Args:
            asset: Base asset (e.g. "BTC").
            leverage: Leverage multiplier.
            margin_mode: "cross" or "isolated".

        Returns:
            Margin config dict.
        """
        config = self.get_margin_config(asset)
        return self.update_margin_config(
            config_id=config["configId"],
            asset=asset,
            leverage=leverage,
            margin_mode=margin_mode,
        )
