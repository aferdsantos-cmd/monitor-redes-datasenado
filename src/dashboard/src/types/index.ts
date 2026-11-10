export type ThemeId = 'eleicao_presidencia_senado' | 'pec_escala_6x1' | 'pl_ia_2338' | string;

export type TimeWindow = '24h' | '7d' | '15d' | '30d' | 'custom';

export type PlatformId =
  | 'youtube'
  | 'telegram'
  | 'x_twitter'
  | 'instagram_facebook'
  | 'tiktok'
  | 'whatsapp';

export type Stance = 'FAVORAVEL' | 'CONTRARIO' | 'NEUTRO' | 'QUARENTENA_CIB';

export interface PlatformConfig {
  id: PlatformId;
  label: string;
  shortLabel: string;
  icon: string;
  color: string;
}

export interface ScenarioResult {
  scenarioId: 'bruto' | 'cenario_1_hajek' | 'cenario_2_equal' | 'cenario_3_raking' | 'rogan_gladen';
  name: string;
  shortName: string;
  description: string;
  favoravel: number; // Percentage
  favoravelCi: [number, number]; // [min, max]
  contrario: number;
  contrarioCi: [number, number];
  neutro: number;
  neutroCi: [number, number];
  formula?: string;
  biasNote?: string;
}

export interface MedallionMetrics {
  bronzeTotal: number;
  queriesUsed: string[];
  silverSpam: number;
  silverCibBots: number;
  silverBotAccounts: number;
  artificialityRate: number; // e.g. 24.5%
  uOrgAccounts: number;
  goldSampleSize: number;
  kishDeff: number;
  nEffective: number;
  marginOfError: number; // e.g. ±3.8 pp
  psiDrift: number;
  psiStatus: 'ESTAVEL' | 'ALERTA' | 'CRITICO';
  youdenJ: number;
  cohenKappa: number;
  sensitivity: number; // Se
  specificity: number; // Sp
}

export interface PlatformBreakdown {
  platformId: PlatformId;
  platformName: string;
  nOrg: number;
  sharePercent: number;
  favoravel: number;
  contrario: number;
  neutro: number;
  cibBlockedCount: number;
}

export interface RegionRakingDiagnostic {
  region: string;
  ufs: string[];
  targetIbgePercent: number;
  obtainedPercent: number;
  gapPp: number;
  weightsSimplexRange: [number, number];
  status: 'CALIBRADO_OK' | 'AJUSTE_LEVE' | 'DISCREPANCIA';
}

export interface AuditRecord {
  id: string; // HMAC-SHA256 truncated
  timestampUtc: string;
  platform: PlatformId;
  region: string;
  uf: string;
  sanitizedText: string;
  stance: Stance;
  confidenceScore: number;
  spectrumId: string;
  spectrumName: string;
  decisiveTerms: string[];
  shapDetails: {
    baseProbability: number;
    predictedProbability: number;
    features: {
      token: string;
      weight: number; // positive or negative
      impactsStance: Stance;
    }[];
  };
}

export interface SpectrumCluster {
  id: string;
  name: string;
  colorHex: string;
  accountCount: number;
  shareOrg: number;
  favoravel: number;
  contrario: number;
  neutro: number;
  seedAccountsCount: number;
  keyArguments: string[];
  topDomains: string[];
  homophilyScore: number;
}

export interface BubbleGraphNode {
  id: string;
  label: string;
  spectrumId: string;
  radius: number;
  x: number;
  y: number;
  isSeed?: boolean;
  isBridge?: boolean;
  participationCoefficient?: number; // Guimerà-Amaral Pi
  degree: number;
}

export interface BubbleGraphEdge {
  source: string;
  target: string;
  weight: number;
  isCrossSpectrum?: boolean;
}

export interface FirstMoverEvent {
  timeStr: string;
  spectrumId: string;
  spectrumName: string;
  postCount: number;
  narrativeHeadline: string;
  isSpamPurgedNote?: string;
}

export interface ConsensusBridge {
  topic: string;
  spectrumsInAgreement: string[];
  description: string;
  supportLevel: string;
}

export interface DivergencePoint {
  topic: string;
  opposingFields: string[];
  description: string;
  tensionLevel: string;
}

export interface TopTermItem {
  term: string;
  mentions: number;
  sharePercent: number;
  predominantStance: 'FAVORAVEL' | 'CONTRARIO' | 'NEUTRO';
}

export interface PressHighlight {
  outlet: string;
  headline: string;
  dateStr: string;
  framing: string;
  repercussionSummary: string;
}

export interface InfluentialProfileCluster {
  name: string;
  platform: string;
  category: string;
  stance: 'FAVORAVEL' | 'CONTRARIO' | 'NEUTRO';
  engagementShare: string;
  coreMessage: string;
}

export interface WatchpointItem {
  title: string;
  riskOrOpportunity: 'ALERTA' | 'TENDENCIA' | 'AGENDA_LEGISLATIVA';
  horizon: string;
  description: string;
}

export interface BoilingTopic {
  id: string;
  title: string;
  committee: string;
  isSenateInterest: boolean;
  relevanceScore: number; // 0-100
  burstinessGohBarabasi: number; // B coefficient
  growth24h: number; // +240%
  volume24h: number;
  cusumTriggered: boolean;
  suggestedAction: string;
  themeIdTarget?: string;
}

export interface ThematicAxis {
  id: string;
  name: string;
  sharePostsPercent: number;
  shareInteractionsPercent: number;
  dominantField: string;
  summary: string;
}

export interface FieldNarrativeDispute {
  fieldId: string;
  fieldName: string;
  colorHex: string;
  shareWithinTheme: number;
  centralFrame: string;
  detailedNarrative: string;
  keyHashtagsOrTerms: string[];
}

export interface ThemeNarrativeInsights {
  executiveLead: string;
  scenariosFinding: string;
  platformsFinding: string;
  regionalFinding: string;
  bubblesFinding: string;
  firstMoverFinding: string;
  legislativeConclusion: string;
  thematicAxes: ThematicAxis[];
  fieldDisputes: FieldNarrativeDispute[];
}

export interface ThemeDataset {
  id: ThemeId;
  title: string;
  subtitle: string;
  committee: string;
  legislativeContext: string;
  statusTag: string;
  narrativeInsights: ThemeNarrativeInsights;
  medallion: MedallionMetrics;
  scenarios: ScenarioResult[];
  platforms: PlatformBreakdown[];
  homogeneityTest: {
    chi2Adjusted: number;
    pValue: number;
    fdrCorrected: boolean;
    cramerV: number;
    interpretation: string;
  };
  rakingDiagnostics: RegionRakingDiagnostic[];
  auditRecords: AuditRecord[];
  topological: {
    modularityObserved: number;
    modularityNull: number;
    zScore: number;
    pValue: number;
    homophilyKrackhardtEI: number;
    homophilyCategory: 'CÂMARA DE ECO FECHADA' | 'MODERADA' | 'DEBATE TRANSVERSAL';
    crossBubbleBridgeRate: number; // % Pi > 0.30
  };
  spectrums: SpectrumCluster[];
  bubbleNodes: BubbleGraphNode[];
  bubbleEdges: BubbleGraphEdge[];
  grangerCausality: {
    fStatistic: number;
    pValue: number;
    optimalLagHours: number;
    firstMoverSpectrumName: string;
    timeline: FirstMoverEvent[];
  };
  consensusBridges: ConsensusBridge[];
  divergencePoints: DivergencePoint[];
  topTerms: TopTermItem[];
  pressHighlights: PressHighlight[];
  influentialProfiles: InfluentialProfileCluster[];
  watchpoints: WatchpointItem[];
  lifecycleStatus?: LifecycleStatus;
  lifecycleProgressPercent?: number;
  connectorSessions?: ConnectorSessionInfo[];
  rateLimitAlert?: RateLimitAlertInfo;
  subrepresentationAlert?: { region: string; n: number; message: string };
  humanGates?: HumanGatesState;
  bronzeSampleRecords?: BronzeSampleRecord[];
  silverQuarantineRecords?: SilverQuarantineRecord[];
  silverOrganicRecords?: SilverOrganicRecord[];
  goldSampleUnits?: GoldSampleUnit[];
  blindAuditItems?: BlindHumanAuditItem[];
  humanCalibration?: HumanCalibrationMetrics;
}

export type LifecycleStatus =
  | 'CADASTRADO_AGUARDANDO_DISPARO'
  | 'VALIDANDO_SESSOES_CONECTORES'
  | 'COLETA_EM_ANDAMENTO_6_REDES'
  | 'DESCONTAMINACAO_SILVER_CIB_SPAM'
  | 'CALIBRACAO_RAKING_IPF_ROGAN_GLADEN'
  | 'PRONTO_PARA_ANALISE_E_BOLETIM'
  | 'ALERTA_OPERACIONAL_BACKOFF_OU_CREDENCIAIS';

export type HumanGateStatus =
  | 'PENDENTE_APROVACAO_HUMANA'
  | 'APROVADO_PELO_ANALISTA'
  | 'REJEITADO_REPROCESSANDO'
  | 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR';

export interface HumanGateInfo {
  gateId: string;
  name: string;
  status: HumanGateStatus;
  approvedAt?: string | null;
  approvedBy?: string | null;
  rejectionReason?: string | null;
  notes?: string;
  excludedRecordIds?: string[];
  overriddenToOrganicIds?: string[];
  overriddenToQuarantineIds?: string[];
  randomSeed?: number;
  targetSampleSize?: number;
  // Aliases snake_case para contrato bidirecional seguro
  gate_id?: string;
  approved_at?: string | null;
  approved_by?: string | null;
  rejection_reason?: string | null;
  excluded_record_ids?: string[];
  overridden_to_organic_ids?: string[];
  overridden_to_quarantine_ids?: string[];
  random_seed?: number;
  target_sample_size?: number;
}

export interface HumanGatesState {
  bronzeGate: HumanGateInfo;
  silverGate: HumanGateInfo;
  goldGate: HumanGateInfo;
  // Aliases snake_case para contrato bidirecional seguro
  bronze_gate?: HumanGateInfo;
  silver_gate?: HumanGateInfo;
  gold_gate?: HumanGateInfo;
}

export function normalizeHumanGates(rawGates?: Partial<HumanGatesState> | Record<string, unknown> | null): HumanGatesState {
  if (!rawGates) {
    const b: HumanGateInfo = {
      gateId: 'gate_1_bronze',
      name: 'Portão 1 — Amostra Bruta (Bronze)',
      status: 'PENDENTE_APROVACAO_HUMANA',
      excludedRecordIds: [],
    };
    const s: HumanGateInfo = {
      gateId: 'gate_2_silver',
      name: 'Portão 2 — Limpeza CIB & Spam (Silver)',
      status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      overriddenToOrganicIds: [],
      overriddenToQuarantineIds: [],
    };
    const g: HumanGateInfo = {
      gateId: 'gate_3_gold',
      name: 'Portão 3 — Amostra Limpa & Ponderação (Gold)',
      status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      randomSeed: 42,
      targetSampleSize: 550,
    };
    return {
      bronzeGate: b,
      bronze_gate: b,
      silverGate: s,
      silver_gate: s,
      goldGate: g,
      gold_gate: g,
    };
  }

  const rawBronze = rawGates.bronzeGate || rawGates.bronze_gate || {};
  const rawSilver = rawGates.silverGate || rawGates.silver_gate || {};
  const rawGold = rawGates.goldGate || rawGates.gold_gate || {};

  const bGate: HumanGateInfo = {
    gateId: rawBronze.gateId || rawBronze.gate_id || 'gate_1_bronze',
    name: rawBronze.name || 'Portão 1 — Amostra Bruta (Bronze)',
    status: rawBronze.status || 'PENDENTE_APROVACAO_HUMANA',
    approvedAt: rawBronze.approvedAt || rawBronze.approved_at || null,
    approvedBy: rawBronze.approvedBy || rawBronze.approved_by || null,
    rejectionReason: rawBronze.rejectionReason || rawBronze.rejection_reason || null,
    notes: rawBronze.notes || '',
    excludedRecordIds: rawBronze.excludedRecordIds || rawBronze.excluded_record_ids || [],
  };

  const sGate: HumanGateInfo = {
    gateId: rawSilver.gateId || rawSilver.gate_id || 'gate_2_silver',
    name: rawSilver.name || 'Portão 2 — Limpeza CIB & Spam (Silver)',
    status: rawSilver.status || 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
    approvedAt: rawSilver.approvedAt || rawSilver.approved_at || null,
    approvedBy: rawSilver.approvedBy || rawSilver.approved_by || null,
    rejectionReason: rawSilver.rejectionReason || rawSilver.rejection_reason || null,
    notes: rawSilver.notes || '',
    overriddenToOrganicIds: rawSilver.overriddenToOrganicIds || rawSilver.overridden_to_organic_ids || [],
    overriddenToQuarantineIds: rawSilver.overriddenToQuarantineIds || rawSilver.overridden_to_quarantine_ids || [],
  };

  const gGate: HumanGateInfo = {
    gateId: rawGold.gateId || rawGold.gate_id || 'gate_3_gold',
    name: rawGold.name || 'Portão 3 — Amostra Limpa & Ponderação (Gold)',
    status: rawGold.status || 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
    approvedAt: rawGold.approvedAt || rawGold.approved_at || null,
    approvedBy: rawGold.approvedBy || rawGold.approved_by || null,
    rejectionReason: rawGold.rejectionReason || rawGold.rejection_reason || null,
    notes: rawGold.notes || '',
    randomSeed: Number(rawGold.randomSeed ?? rawGold.random_seed ?? 42),
    targetSampleSize: Number(rawGold.targetSampleSize ?? rawGold.target_sample_size ?? 550),
  };

  return {
    bronzeGate: bGate,
    bronze_gate: bGate,
    silverGate: sGate,
    silver_gate: sGate,
    goldGate: gGate,
    gold_gate: gGate,
  };
}

export interface BronzeSampleRecord {
  id: string;
  timestampUtc: string;
  platform: PlatformId;
  uf: string;
  queryUsed: string;
  rawText: string;
  isExcluded: boolean;
}

export interface SilverQuarantineRecord {
  id: string;
  timestampUtc: string;
  platform: PlatformId;
  uf: string;
  reasonTag: string;
  reasonDescription: string;
  rawText: string;
  isRescuedOrganic: boolean;
}

export interface SilverOrganicRecord {
  id: string;
  authorIdHash: string;
  timestampUtc: string;
  platform: PlatformId;
  uf: string;
  postCount: number;
  sanitizedSnippet: string;
  isManualQuarantine: boolean;
}

export interface GoldSampleUnit {
  id: string;
  authorIdHash: string;
  platform: PlatformId;
  uf: string;
  macroregion: string;
  postsCollapsed: number;
  hajekWeight: number;
  rakingWeight: number;
  sanitizedText: string;
  stance: Stance;
}

export interface BlindHumanAuditItem {
  id: string;
  sanitizedText: string;
  platform: PlatformId;
  uf: string;
  aiPredictedStance: Stance;
  aiConfidence: number;
  aiKeyTerms: string[];
  humanStance?: Stance;
  match?: boolean;
}

export interface ConfusionMatrix3x3 {
  favoravel: { favoravel: number; contrario: number; neutro: number };
  contrario: { favoravel: number; contrario: number; neutro: number };
  neutro: { favoravel: number; contrario: number; neutro: number };
}

export interface HumanCalibrationMetrics {
  totalAudited: number;
  confusionMatrix: ConfusionMatrix3x3;
  cohenKappa: number;
  sensitivity: number;
  specificity: number;
  youdenJ: number;
  roganGladenPrevalence: number;
  matchRate: number;
}

export interface SandboxStepResult {
  step1_lgpd: {
    original_text: string;
    scrubbed_text: string;
    author_id_hash: string;
    author_pii_cleared: boolean;
    protocol: string;
  };
  step2_silver_cib: {
    minhash_signature: string;
    commercial_spam_score: number;
    burstiness_index: number;
    verdict: 'ORGANICO' | 'QUARENTENA';
    reason_tag: string;
  };
  step3_feature_engineering: {
    token_count: number;
    lexical_bias_score: number;
    framing_detected: string;
    bias_terms_found: string[];
  };
  step4_classifier_xai: {
    probabilities: { favoravel: number; contrario: number; neutro: number };
    predicted_stance: Stance;
    shap_tokens: { token: string; weight: number; impacts_stance: Stance }[];
  };
  step5_digital_spectrum: {
    primary_spectrum_id: string;
    primary_spectrum_name: string;
    harmonic_affinity: Record<string, number>;
  };
  step6_sample_weighting: {
    single_account_weight_hajek: number;
    macroregion: string;
    raking_ipf_weight: number;
    simplex_clipped: boolean;
    rogan_gladen_formula: string;
    rogan_gladen_impact: string;
  };
}

export interface ConnectorSessionInfo {
  platformId: PlatformId;
  platformName: string;
  status: 'CONECTADO_HTTP_200' | 'COOKIE_EXPIRANDO_AVISO' | 'REQUER_RENOVACAO_HTTP_401_403' | 'PAUSA_PREVENTIVA_RATE_LIMIT_HTTP_429';
  authType: 'PUBLIC_REVERSE_API' | 'SESSION_COOKIE' | 'MTPROTO_DAEMON' | 'QR_CODE_PAIRING';
  lastPingUtc: string;
  maskedCredentialHint: string;
  jitterRangeSeconds: [number, number];
  rateLimitBackoffSeconds?: number;
  remainingQuotaEstimate?: number;
}

export interface RateLimitAlertInfo {
  platformId: PlatformId;
  platformName: string;
  backoffSecondsRemaining: number;
  suggestedAction: string;
  isKishSubrepresented?: boolean;
  affectedMacroregion?: string;
  currentSampleSize?: number;
}

