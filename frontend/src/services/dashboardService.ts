import {
  DashboardMetrics,
  RecoveryCaseSummary,
  AgentActivity,
  RevenueTrendPoint,
  StrategyPerformance,
} from '../types/dashboard';

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

function getAuthHeaders(): HeadersInit {
  const saved = localStorage.getItem('recoverai_auth_session');
  if (saved) {
    try {
      const parsed = JSON.parse(saved);
      if (parsed?.token) {
        return {
          Authorization: `Bearer ${parsed.token}`,
          'Content-Type': 'application/json',
        };
      }
    } catch {
      // fallback
    }
  }
  return { 'Content-Type': 'application/json' };
}

export const mockRecentActivities: AgentActivity[] = [
  {
    id: 'ACT-001',
    timestamp: '14:34:22',
    eventType: 'PAYMENT_VERIFIED',
    description: 'Payment verified for C1024 — ₹1,999 recovered via Payment Link',
    status: 'success',
    caseId: 'rec_c1024_fail',
    amount: 1999,
  },
  {
    id: 'ACT-002',
    timestamp: '14:32:08',
    eventType: 'ACTION_EXECUTED',
    description: 'Autonomous payment link dispatched to customer C1024',
    status: 'info',
    caseId: 'rec_c1024_fail',
  },
  {
    id: 'ACT-003',
    timestamp: '14:32:07',
    eventType: 'STRATEGY_SELECTED',
    description: 'AI selected CREATE_PAYMENT_LINK (87.8% ML confidence, card decline)',
    status: 'info',
    caseId: 'rec_c1024_fail',
  },
];

export async function fetchDashboardMetrics(): Promise<DashboardMetrics> {
  try {
    const res = await fetch(`${API_BASE}/analytics/overview`, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      return {
        revenueAtRisk: Math.round(data.revenue_at_risk_paise / 100),
        estimatedRecoverable: Math.round(data.estimated_recoverable_paise / 100),
        revenueRecovered: Math.round((data.revenue_recovered_paise || 0) / 100),
        recoveryRate: data.failure_rate,
        activeCases: data.failed_payment_count,
        successfulActions: data.success_payment_count,
        casesAnalyzed: data.total_payment_count,
        escalatedCases: 0,
      };
    }
  } catch (err) {
    console.warn('Backend /analytics/overview unavailable, using fallback:', err);
  }

  return {
    revenueAtRisk: 11946257,
    estimatedRecoverable: 9199741,
    revenueRecovered: 0,
    recoveryRate: 7.50,
    activeCases: 1624,
    successfulActions: 20024,
    casesAnalyzed: 21648,
    escalatedCases: 0,
  };
}

export async function fetchPayments(
  page = 1,
  limit = 20,
  status?: string,
  search?: string
): Promise<{ items: any[]; total: number }> {
  try {
    let url = `${API_BASE}/payments?page=${page}&limit=${limit}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (search) url += `&customer_id=${encodeURIComponent(search)}`;

    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      return {
        items: data.items.map((p: any) => ({
          id: p.id,
          customerId: p.customer_id,
          amount: Math.round(p.amount / 100),
          currency: p.currency,
          paymentMethod: p.payment_method,
          status: p.status,
          failureReason: p.failure_reason,
          createdAt: p.created_at,
        })),
        total: data.total,
      };
    }
  } catch (err) {
    console.warn('Backend /payments unavailable, using fallback:', err);
  }

  return { items: [], total: 0 };
}

export async function fetchCustomers(
  page = 1,
  limit = 50,
  search?: string
): Promise<{ items: any[]; total: number }> {
  try {
    let url = `${API_BASE}/customers?page=${page}&limit=${limit}`;
    if (search) url += `&search=${encodeURIComponent(search)}`;

    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      return {
        items: data.items.map((c: any) => ({
          id: c.id,
          merchantId: c.merchant_id,
          demoName: c.demo_name,
          subscriptionValue: Math.round(c.subscription_value / 100),
          tenure: c.tenure,
          activityScore: c.activity_score,
          createdAt: c.created_at,
        })),
        total: data.total,
      };
    }
  } catch (err) {
    console.warn('Backend /customers unavailable:', err);
  }

  return { items: [], total: 0 };
}

export async function fetchRecoveryCases(
  page = 1,
  limit = 20,
  status?: string,
  strategy?: string
): Promise<{ items: RecoveryCaseSummary[]; total: number }> {
  try {
    let url = `${API_BASE}/recovery-cases?page=${page}&limit=${limit}`;
    if (status) url += `&status=${encodeURIComponent(status)}`;
    if (strategy) url += `&selected_strategy=${encodeURIComponent(strategy)}`;

    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      return {
        items: data.items.map((item: any) => ({
          id: item.id,
          customerId: item.customer_id || item.customer?.id || item.payment?.customer_id || 'Unknown',
          customerName: item.customer?.demo_name || 'Enterprise Customer',
          amount: Math.round(item.expected_revenue / 100),
          currency: item.payment?.currency || 'INR',
          failureReason: item.payment?.failure_reason || 'Payment Failure',
          paymentMethod: item.payment?.payment_method || 'card',
          recoveryProbability: item.recovery_probability ? Math.round(item.recovery_probability * 100) : 70,
          selectedStrategy: item.selected_strategy || 'RETRY_PAYMENT',
          status: item.status,
          recoveredAmount: item.recovered_amount ? Math.round(item.recovered_amount / 100) : 0,
          createdAt: item.created_at,
        })),
        total: data.total,
      };
    }
  } catch (err) {
    console.warn('Backend /recovery-cases unavailable:', err);
  }

  return { items: [], total: 0 };
}

export async function fetchRecoveryCasesPreview(): Promise<RecoveryCaseSummary[]> {
  const { items } = await fetchRecoveryCases(1, 5);
  return items;
}

export async function predictRecoveryProbability(paymentId: string): Promise<any> {
  return predictRecovery(paymentId);
}

export async function predictRecovery(paymentId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/ai/predict-recovery`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ payment_id: paymentId }),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Predict recovery call failed:', err);
  }
  return null;
}

export async function executeRecoveryWorkflow(caseId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/ai/recover/${caseId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({}),
    });
    if (res.ok) {
      return await res.json();
    }
    const errData = await res.json();
    throw new Error(errData.detail || 'Recovery execution failed.');
  } catch (err: any) {
    throw err;
  }
}

export async function fetchAiDecisions(limit = 50): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/ai/decisions?limit=${limit}`, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      if (Array.isArray(data)) {
        return data
          .filter((ev: any) => {
            // Strictly exclude memory-learning events and non-decision audit records
            if (ev.event_type === 'AGENT_MEMORY_LEARNED' || ev.actor === 'adaptive_memory_engine_v1') {
              return false;
            }
            if (ev.id?.startsWith('aud_mem_') || ev.recovery_case_id?.startsWith('mem_')) {
              return false;
            }
            return (
              ev.event_type?.startsWith('RECOVERY_') ||
              ev.event_type?.startsWith('SIMULATOR_') ||
              ev.actor === 'ai_recovery_agent_v1' ||
              ev.actor === 'autonomous_simulator_engine_v1' ||
              ev.recovery_case_id?.startsWith('rec_') ||
              ev.metadata?.recovery_case_id?.startsWith('rec_')
            );
          })
          .map((ev: any) => {
            const meta = ev.metadata || {};
            const rawProb = meta.ml_probability;
            let probFormatted = '—';
            if (rawProb !== undefined && rawProb !== null) {
              const num = Number(rawProb);
              if (!isNaN(num)) {
                probFormatted = num <= 1.0 ? (num * 100).toFixed(1) : num.toFixed(1);
              }
            } else if (meta.confidence !== undefined && meta.confidence !== null) {
              const num = Number(meta.confidence);
              if (!isNaN(num)) {
                probFormatted = num <= 1.0 ? (num * 100).toFixed(1) : num.toFixed(1);
              }
            }

            const strategy =
              meta.selected_strategy ||
              ev.event_type?.replace('RECOVERY_', '').replace('SIMULATOR_', '') ||
              'RECOVERY_ACTION';

            const customerId =
              meta.customer_id ||
              (ev.recovery_case_id?.startsWith('rec_c')
                ? ev.recovery_case_id.split('_')[1]?.toUpperCase()
                : '—');

            // Actual RecoveryAction ID (e.g. act_c1418_7_3_dabeecff from aud_act_c1418_7_3_dabeecff)
            const actionId =
              ev.id?.startsWith('aud_act_')
                ? ev.id.replace('aud_', '')
                : meta.recovery_action_id || ev.id;

            const toolInvoked =
              meta.tool_invoked ||
              (strategy === 'RETRY_PAYMENT'
                ? 'payment_retry_simulator'
                : strategy === 'CREATE_PAYMENT_LINK'
                ? 'payment_link_simulator'
                : strategy === 'ALTERNATE_PAYMENT_METHOD'
                ? 'payment_method_update_simulator'
                : strategy === 'SEND_REMINDER'
                ? 'customer_notification_simulator'
                : strategy === 'OFFER_INCENTIVE'
                ? 'incentive_offer_simulator'
                : strategy === 'ESCALATE_TO_HUMAN'
                ? 'human_escalation_tool'
                : 'autonomous_engine');

            const decisionReason =
              meta.agent_reason ||
              meta.decision_reason ||
              meta.reason ||
              `AI Agent selected ${strategy.replace(/_/g, ' ')} based on ML score and failure taxonomy.`;

            const toolResult =
              meta.tool_result ||
              (meta.is_recovered === true
                ? 'SUCCESS'
                : meta.is_recovered === false
                ? 'FAILED'
                : 'EXECUTED');

            const currentStatus =
              meta.state_transition?.includes('-> RECOVERED') || toolResult === 'SUCCESS'
                ? 'RECOVERED'
                : meta.state_transition?.includes('-> ESCALATED')
                ? 'ESCALATED'
                : toolResult === 'FAILED'
                ? 'FAILED'
                : 'ACTION_EXECUTED';

            return {
              id: ev.id,
              recovery_case_id: ev.recovery_case_id || meta.recovery_case_id || 'rec_case',
              customer_id: customerId,
              ml_probability_percentage: probFormatted,
              selected_strategy: strategy,
              tool_invoked: toolInvoked,
              decision_reason: decisionReason,
              current_status: currentStatus,
              tool_result: toolResult,
              recovery_action_id: actionId,
              created_at: ev.created_at,
            };
          });
      }
    }
  } catch (err) {
    console.warn('Backend /ai/decisions unavailable:', err);
  }
  return [];
}

export async function fetchRecoveryCaseWorkflow(caseId: string): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/ai/recovery-case/${caseId}/workflow`, {
      headers: getAuthHeaders(),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /ai/recovery-case workflow unavailable:', err);
  }
  return null;
}

// Phase 7 Simulator Endpoints
export async function fetchSimulatorStatus(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/simulator/status`, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /simulator/status unavailable:', err);
  }
  return null;
}

export async function runBatchSimulation(batchSize = 25, scenario = 'auto'): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/simulator/run`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ batch_size: batchSize, scenario }),
    });
    if (res.ok) {
      return await res.json();
    }
    const err = await res.json();
    throw new Error(err.detail || 'Batch simulation failed.');
  } catch (err: any) {
    throw err;
  }
}

export async function simulateSingleCase(caseId: string, scenario = 'auto'): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/simulator/case/${caseId}`, {
      method: 'POST',
      headers: getAuthHeaders(),
      body: JSON.stringify({ scenario }),
    });
    if (res.ok) {
      return await res.json();
    }
    const err = await res.json();
    throw new Error(err.detail || 'Single case simulation failed.');
  } catch (err: any) {
    throw err;
  }
}

export async function resetSimulator(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/simulator/reset`, {
      method: 'POST',
      headers: getAuthHeaders(),
    });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Simulator reset failed:', err);
  }
  return null;
}

// Phase 8 Adaptive Memory Endpoints
export async function fetchMemoryStatus(): Promise<any> {
  try {
    const res = await fetch(`${API_BASE}/ai/memory/status`, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /ai/memory/status unavailable:', err);
  }
  return null;
}

export async function fetchStrategyPerformance(): Promise<StrategyPerformance[]> {
  try {
    const res = await fetch(`${API_BASE}/ai/memory/performance`, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      if (data && data.length > 0) {
        return data.map((item: any) => ({
          strategy: item.strategy,
          label: item.label,
          count: item.total_attempts,
          recoveredAmount: item.recovered_amount_inr,
          successRate: item.recovery_rate,
        }));
      }
    }
  } catch (err) {
    console.warn('Backend /ai/memory/performance unavailable, fallback to default:', err);
  }

  return [
    { strategy: 'CREATE_PAYMENT_LINK', label: 'Payment Link', count: 320, recoveredAmount: 1340000, successRate: 68.5 },
    { strategy: 'RETRY_PAYMENT', label: 'Smart Retry', count: 280, recoveredAmount: 980000, successRate: 59.2 },
    { strategy: 'ALTERNATE_PAYMENT_METHOD', label: 'Alternate Method', count: 185, recoveredAmount: 510000, successRate: 46.1 },
    { strategy: 'SEND_REMINDER', label: 'Personalized Reminder', count: 120, recoveredAmount: 220000, successRate: 38.0 },
    { strategy: 'OFFER_INCENTIVE', label: 'Dynamic Incentive', count: 45, recoveredAmount: 70000, successRate: 32.4 },
  ];
}

export async function fetchRelevantMemory(
  failureReason: string,
  activityScore = 0.5,
  tenure = 6
): Promise<any> {
  try {
    const url = `${API_BASE}/ai/memory/relevant?failure_reason=${encodeURIComponent(
      failureReason
    )}&activity_score=${activityScore}&tenure=${tenure}&limit=5`;
    const res = await fetch(url, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /ai/memory/relevant unavailable:', err);
  }
  return null;
}

export async function fetchFailureReasons(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/failure-reasons`, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /analytics/failure-reasons unavailable:', err);
  }
  return [];
}

export async function fetchPaymentMethods(): Promise<any[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/payment-methods`, { headers: getAuthHeaders() });
    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Backend /analytics/payment-methods unavailable:', err);
  }
  return [];
}

function formatTrendDateLabel(dateStr: string): string {
  if (!dateStr) return '';
  const monthNames = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
  const parts = dateStr.split('-');
  if (parts.length === 3) {
    const monthIdx = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    if (monthIdx >= 0 && monthIdx < 12 && !isNaN(day)) {
      return `${monthNames[monthIdx]} ${day}`;
    }
  }
  if (parts.length === 2) {
    const monthIdx = parseInt(parts[0], 10) - 1;
    const day = parseInt(parts[1], 10);
    if (monthIdx >= 0 && monthIdx < 12 && !isNaN(day)) {
      return `${monthNames[monthIdx]} ${day}`;
    }
  }
  return dateStr;
}

export async function fetchRevenueTrends(): Promise<RevenueTrendPoint[]> {
  try {
    const res = await fetch(`${API_BASE}/analytics/trends?period=daily&limit=14`, { headers: getAuthHeaders() });
    if (res.ok) {
      const data = await res.json();
      if (data && data.length > 0) {
        return data.map((t: any) => ({
          date: formatTrendDateLabel(t.date),
          recovered: Math.round(t.success_volume_paise / 100),
          atRisk: Math.round(t.at_risk_paise / 100),
        }));
      }
    }
  } catch (err) {
    console.warn('Backend /analytics/trends unavailable:', err);
  }

  return [
    { date: 'Jan 1', atRisk: 1200000, recovered: 680000 },
    { date: 'Jan 2', atRisk: 1450000, recovered: 820000 },
    { date: 'Jan 3', atRisk: 1100000, recovered: 610000 },
    { date: 'Jan 4', atRisk: 1600000, recovered: 940000 },
    { date: 'Jan 5', atRisk: 1350000, recovered: 780000 },
    { date: 'Jan 6', atRisk: 900000, recovered: 510000 },
    { date: 'Jan 7', atRisk: 750000, recovered: 420000 },
  ];
}

export async function fetchRecentActivities(): Promise<AgentActivity[]> {
  return mockRecentActivities;
}
