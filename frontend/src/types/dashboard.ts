export type RecoveryStatus =
  | 'RECOVERED'
  | 'AT_RISK'
  | 'ANALYZING'
  | 'RECOVERY_ACTIVE'
  | 'FAILED'
  | 'ESCALATED';

export type RecoveryStrategy =
  | 'RETRY_PAYMENT'
  | 'CREATE_PAYMENT_LINK'
  | 'ALTERNATE_PAYMENT_METHOD'
  | 'SEND_REMINDER'
  | 'OFFER_INCENTIVE'
  | 'ESCALATE_TO_HUMAN';

export interface DashboardMetrics {
  revenueAtRisk: number;
  estimatedRecoverable: number;
  revenueRecovered: number;
  recoveryRate: number; // e.g. 55.3
  activeCases: number;
  successfulActions: number;
  casesAnalyzed: number;
  escalatedCases: number;
}

export interface RecoveryCaseSummary {
  id: string;
  customerId: string;
  customerName: string;
  amount: number;
  currency: string;
  failureReason: string;
  paymentMethod: string;
  recoveryProbability: number;
  selectedStrategy: RecoveryStrategy;
  status: RecoveryStatus;
  recoveredAmount?: number;
  createdAt: string;
}

export interface AgentActivity {
  id: string;
  timestamp: string;
  eventType: string;
  description: string;
  status: 'success' | 'warning' | 'info' | 'error';
  caseId?: string;
  amount?: number;
}

export interface RevenueTrendPoint {
  date: string;
  recovered: number;
  atRisk: number;
}

export interface StrategyPerformance {
  strategy: RecoveryStrategy;
  label: string;
  count: number;
  recoveredAmount: number;
  successRate: number;
}
