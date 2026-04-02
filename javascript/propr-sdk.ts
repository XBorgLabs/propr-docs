/**
 * Propr TypeScript/JavaScript SDK
 * Official client for the Propr trading API.
 *
 * Usage:
 *   import { ProprClient } from './propr-sdk';
 *
 *   const client = new ProprClient();
 *   await client.setup();
 *   console.log(await client.getPositions());
 */

import { ulid } from 'ulid';

const DEFAULT_BASE_URL = 'https://api.propr.xyz/v1';

// ── Types ──

export interface ProprClientOptions {
  apiKey?: string;
  baseUrl?: string;
  timeout?: number;
}

export interface Order {
  orderId: string;
  intentId: string;
  orderGroupId: string | null;
  exchangeOrderId: string | null;
  userId: string;
  accountId: string;
  positionId: string | null;
  exchange: string;
  productType: string;
  asset: string;
  base: string;
  quote: string;
  type: string;
  side: string;
  positionSide: string;
  timeInForce: string;
  quantity: string;
  price: string | null;
  triggerPrice: string | null;
  closePosition: boolean;
  reduceOnly: boolean;
  cumulativeQuantity: string;
  cumulativeQuote: string;
  averageFillPrice: string | null;
  cumulativeTradingFees: string;
  tradingFeeRate: string;
  expiresAt: string | null;
  filledAt: string | null;
  cancelledAt: string | null;
  status: string;
  createdAt: string;
  updatedAt: string;
}

export interface Position {
  positionId: string;
  userId: string;
  accountId: string;
  exchange: string;
  productType: string;
  status: string;
  asset: string;
  base: string;
  quote: string;
  positionSide: string;
  leverage: string;
  marginMode: string;
  quantity: string;
  entryPrice: string;
  breakEvenPrice: string;
  markPrice: string;
  liquidationPrice: string;
  unrealizedPnl: string;
  realizedPnl: string;
  marginUsed: string;
  notionalValue: string;
  cumulativeFunding: string;
  cumulativeTradingFees: string;
  tradingFeeRate: string;
  returnOnEquity: string;
  createdAt: string;
  updatedAt: string;
  closedAt: string | null;
}

export interface Trade {
  tradeId: string;
  userId: string;
  accountId: string;
  orderId: string;
  positionId: string;
  exchangeTradeId: string | null;
  transactionHash: string | null;
  exchange: string;
  productType: string;
  type: string;
  liquidityType: string;
  asset: string;
  base: string;
  quote: string;
  side: string;
  positionSide: string;
  quantity: string;
  price: string;
  quoteQuantity: string;
  fee: string;
  feeAsset: string;
  feeRate: string;
  leverage: string;
  marginMode: string;
  realizedPnl: string;
  positionSizeBefore: string;
  slippage: string;
  markPriceAtOrder: string;
  isLiquidation: boolean;
  executedAt: string;
  createdAt: string;
}

export interface MarginConfig {
  configId: string;
  accountId: string;
  exchange: string;
  asset: string;
  marginMode: string;
  leverage: string;
  createdAt: string;
  updatedAt: string;
}

export interface LeverageLimits {
  defaultMax: number;
  overrides: Record<string, number>;
}

export interface CreateOrderParams {
  side: 'buy' | 'sell';
  positionSide: 'long' | 'short';
  orderType: 'market' | 'limit' | 'stop_market' | 'stop_limit' | 'take_profit_market' | 'take_profit_limit';
  asset: string;
  base: string;
  quote: string;
  quantity: string;
  price?: string;
  triggerPrice?: string;
  timeInForce?: 'GTC' | 'IOC' | 'FOK' | 'GTX';
  reduceOnly?: boolean;
  closePosition?: boolean;
}

// ── Error ──

export class ProprAPIError extends Error {
  statusCode: number;
  code: number | null;

  constructor(statusCode: number, code: number | null, message: string) {
    super(`[${statusCode}] ${code}: ${message}`);
    this.name = 'ProprAPIError';
    this.statusCode = statusCode;
    this.code = code;
  }
}

// ── Client ──

export class ProprClient {
  private apiKey: string;
  private baseUrl: string;
  private timeout: number;
  public accountId: string | null = null;

  constructor(options: ProprClientOptions = {}) {
    this.apiKey =
      options.apiKey ||
      process.env.PROPR_API_KEY ||
      '';
    this.baseUrl =
      options.baseUrl ||
      process.env.PROPR_API_URL ||
      DEFAULT_BASE_URL;
    this.timeout = options.timeout || 30_000;

    if (!this.apiKey) {
      throw new Error(
        'API key required. Set PROPR_API_KEY env var or pass apiKey option.\n' +
        'Get your key at https://app.propr.xyz/settings'
      );
    }
  }

  // ── Internal ──

  private async request<T = any>(
    method: string,
    path: string,
    options: { params?: Record<string, any>; body?: any } = {},
  ): Promise<T> {
    let url = `${this.baseUrl}${path}`;

    if (options.params) {
      const searchParams = new URLSearchParams();
      for (const [key, value] of Object.entries(options.params)) {
        if (value !== undefined && value !== null) {
          searchParams.set(key, String(value));
        }
      }
      const qs = searchParams.toString();
      if (qs) url += `?${qs}`;
    }

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout);

    try {
      const response = await fetch(url, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey,
        },
        body: options.body ? JSON.stringify(options.body) : undefined,
        signal: controller.signal,
      });

      if (!response.ok) {
        let code: number | null = null;
        let message = 'unknown_error';
        try {
          const body = await response.json();
          code = body.code ?? null;
          message = body.message ?? message;
        } catch {}
        throw new ProprAPIError(response.status, code, message);
      }

      return response.json();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  private get<T = any>(path: string, params?: Record<string, any>): Promise<T> {
    return this.request<T>('GET', path, { params });
  }

  private post<T = any>(path: string, body?: any): Promise<T> {
    return this.request<T>('POST', path, { body });
  }

  private put<T = any>(path: string, body?: any): Promise<T> {
    return this.request<T>('PUT', path, { body });
  }

  private accountPath(suffix: string): string {
    if (!this.accountId) {
      throw new Error(
        'accountId not set. Call client.setup() first or set client.accountId manually.'
      );
    }
    return `/accounts/${this.accountId}${suffix}`;
  }

  // ── Setup ──

  async setup(accountId?: string): Promise<string> {
    if (accountId) {
      this.accountId = accountId;
      return this.accountId;
    }

    const attempts = await this.getChallengeAttempts({ status: 'active' });
    if (!attempts.length) {
      throw new Error(
        'No active challenge found. Purchase a challenge at ' +
        'https://app.propr.xyz/dashboard first.'
      );
    }
    this.accountId = attempts[0].accountId;
    return this.accountId;
  }

  // ── Health ──

  async health(): Promise<{ status: string }> {
    return this.get('/health');
  }

  async healthServices(): Promise<{ core: string }> {
    return this.get('/health/services');
  }

  // ── User ──

  async getUser(): Promise<any> {
    return this.get('/users/me');
  }

  // ── Challenges ──

  async getChallenges(params: {
    challengeId?: string;
    productId?: string;
    currency?: string;
    exchange?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<any[]> {
    const res = await this.get<{ data: any[] }>('/challenges', {
      limit: 20,
      offset: 0,
      ...params,
    });
    return res.data ?? [];
  }

  // ── Challenge Attempts ──

  async getChallengeAttempts(params: {
    attemptId?: string;
    challengeId?: string;
    status?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<any[]> {
    const res = await this.get<{ data: any[] }>('/challenge-attempts', {
      limit: 20,
      offset: 0,
      ...params,
    });
    return res.data ?? [];
  }

  async getChallengeAttempt(attemptId: string): Promise<any> {
    return this.get(`/challenge-attempts/${attemptId}`);
  }

  // ── Orders ──

  async getOrders(params: {
    orderId?: string;
    tradeId?: string;
    positionId?: string;
    base?: string;
    quote?: string;
    side?: string;
    status?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<Order[]> {
    const res = await this.get<{ data: Order[] }>(
      this.accountPath('/orders'),
      { limit: 20, offset: 0, ...params },
    );
    return res.data ?? [];
  }

  async createOrder(params: CreateOrderParams): Promise<Order[]> {
    const order: Record<string, any> = {
      accountId: this.accountId,
      intentId: ulid(),
      exchange: 'hyperliquid',
      type: params.orderType,
      side: params.side,
      positionSide: params.positionSide,
      productType: 'perp',
      timeInForce: params.timeInForce ?? (params.orderType === 'market' ? 'IOC' : 'GTC'),
      asset: params.asset,
      base: params.base,
      quote: params.quote,
      quantity: params.quantity,
      reduceOnly: params.reduceOnly ?? false,
      closePosition: params.closePosition ?? false,
    };
    if (params.price !== undefined) order.price = params.price;
    if (params.triggerPrice !== undefined) order.triggerPrice = params.triggerPrice;

    const res = await this.post<{ data: Order[] }>(
      this.accountPath('/orders'),
      { orders: [order] },
    );
    return res.data ?? [];
  }

  async createOrders(orders: Record<string, any>[]): Promise<Order[]> {
    for (const order of orders) {
      if (!order.intentId) order.intentId = ulid();
      if (!order.accountId) order.accountId = this.accountId;
    }

    const res = await this.post<{ data: Order[] }>(
      this.accountPath('/orders'),
      { orders },
    );
    return res.data ?? [];
  }

  async cancelOrder(orderId: string): Promise<Order | null> {
    try {
      return await this.post<Order>(this.accountPath(`/orders/${orderId}/cancel`));
    } catch (err) {
      if (err instanceof ProprAPIError && err.statusCode === 400) {
        return null; // Already filled or cancelled
      }
      throw err;
    }
  }

  async cancelAllOrders(base?: string): Promise<Order[]> {
    const params: Record<string, any> = { status: 'open' };
    if (base) params.base = base;

    const openOrders = await this.getOrders(params);
    const cancelled: Order[] = [];

    for (const order of openOrders) {
      const result = await this.cancelOrder(order.orderId);
      if (result) cancelled.push(result);
    }
    return cancelled;
  }

  // ── Positions ──

  async getPositions(params: {
    positionId?: string;
    asset?: string;
    base?: string;
    quote?: string;
    positionSide?: string;
    status?: string;
    limit?: number;
    offset?: number;
    excludeZero?: boolean;
  } = {}): Promise<Position[]> {
    const { excludeZero = true, ...queryParams } = params;

    const res = await this.get<{ data: Position[] }>(
      this.accountPath('/positions'),
      { limit: 20, offset: 0, ...queryParams },
    );

    let positions = res.data ?? [];
    if (excludeZero) {
      positions = positions.filter((p) => parseFloat(p.quantity) > 0);
    }
    return positions;
  }

  async getOpenPositions(base?: string): Promise<Position[]> {
    return this.getPositions({ base, status: 'open', excludeZero: true });
  }

  // ── Trades ──

  async getTrades(params: {
    tradeId?: string;
    positionId?: string;
    orderId?: string;
    base?: string;
    quote?: string;
    side?: string;
    limit?: number;
    offset?: number;
  } = {}): Promise<Trade[]> {
    const res = await this.get<{ data: Trade[] }>(
      this.accountPath('/trades'),
      { limit: 20, offset: 0, ...params },
    );
    return res.data ?? [];
  }

  // ── Margin Configuration ──

  async getMarginConfig(asset: string): Promise<MarginConfig> {
    return this.get<MarginConfig>(this.accountPath(`/margin-config/${asset}`));
  }

  async updateMarginConfig(
    configId: string,
    asset: string,
    leverage: number,
    marginMode: string = 'cross',
  ): Promise<MarginConfig> {
    return this.put<MarginConfig>(
      this.accountPath(`/margin-config/${configId}`),
      {
        exchange: 'hyperliquid',
        asset,
        marginMode,
        leverage,
      },
    );
  }

  // ── Leverage Limits ──

  async getLeverageLimits(): Promise<LeverageLimits> {
    return this.get<LeverageLimits>('/leverage-limits/effective');
  }

  async maxLeverage(asset: string): Promise<number> {
    const limits = await this.getLeverageLimits();
    return limits.overrides[asset] ?? limits.defaultMax;
  }

  // ── Convenience Methods ──

  async marketBuy(base: string, quantity: string, quote = 'USDC'): Promise<Order[]> {
    return this.createOrder({
      side: 'buy',
      positionSide: 'long',
      orderType: 'market',
      asset: `${base}/${quote}`,
      base,
      quote,
      quantity,
    });
  }

  async marketSell(
    base: string,
    quantity: string,
    quote = 'USDC',
    reduceOnly = true,
  ): Promise<Order[]> {
    return this.createOrder({
      side: 'sell',
      positionSide: 'long',
      orderType: 'market',
      asset: `${base}/${quote}`,
      base,
      quote,
      quantity,
      reduceOnly,
    });
  }

  async limitBuy(
    base: string,
    quantity: string,
    price: string,
    quote = 'USDC',
  ): Promise<Order[]> {
    return this.createOrder({
      side: 'buy',
      positionSide: 'long',
      orderType: 'limit',
      asset: `${base}/${quote}`,
      base,
      quote,
      quantity,
      price,
    });
  }

  async limitSell(
    base: string,
    quantity: string,
    price: string,
    quote = 'USDC',
    reduceOnly = true,
  ): Promise<Order[]> {
    return this.createOrder({
      side: 'sell',
      positionSide: 'long',
      orderType: 'limit',
      asset: `${base}/${quote}`,
      base,
      quote,
      quantity,
      price,
      reduceOnly,
    });
  }

  async closePosition(base: string, quote = 'USDC'): Promise<Order[]> {
    const positions = await this.getOpenPositions(base);
    if (!positions.length) return [];

    const pos = positions[0];
    const closeSide = pos.positionSide === 'long' ? 'sell' : 'buy';

    return this.createOrder({
      side: closeSide as 'buy' | 'sell',
      positionSide: pos.positionSide as 'long' | 'short',
      orderType: 'market',
      asset: `${base}/${quote}`,
      base,
      quote,
      quantity: pos.quantity,
      reduceOnly: true,
      closePosition: true,
    });
  }

  async setLeverage(
    asset: string,
    leverage: number,
    marginMode = 'cross',
  ): Promise<MarginConfig> {
    const config = await this.getMarginConfig(asset);
    return this.updateMarginConfig(config.configId, asset, leverage, marginMode);
  }
}
