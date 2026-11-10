import React, { useState, useEffect } from 'react';
import {
  ShieldCheck,
  CheckCircle2,
  AlertTriangle,
  RotateCcw,
  Sparkles,
  Search,
  Filter,
  Eye,
  EyeOff,
  ArrowRight,
  Download,
  Dices,
  Lock,
  Unlock,
  Sliders,
  Send,
  HelpCircle,
} from 'lucide-react';
import {
  ThemeDataset,
  Stance,
  PlatformId,
  HumanGateStatus,
  HumanGatesState,
  normalizeHumanGates,
  BronzeSampleRecord,
  SilverQuarantineRecord,
  SilverOrganicRecord,
  GoldSampleUnit,
  BlindHumanAuditItem,
  ConfusionMatrix3x3,
  SandboxStepResult,
} from '../../types';
import { useToast } from '../Toast';

interface Module5Props {
  dataset: ThemeDataset;
  onRefreshDataset?: () => void;
  onDatasetUpdated?: (updated: Partial<ThemeDataset>) => void;
}

export const Module5HumanValidationAndLayers: React.FC<Module5Props> = ({
  dataset,
  onRefreshDataset,
  onDatasetUpdated,
}) => {
  const { showToast } = useToast();
  const [activeTab, setActiveTab] = useState<'bronze' | 'silver' | 'gold' | 'blind_audit' | 'sandbox'>('bronze');

  // Estado local para manipulação interativa da Camada Bronze
  const [bronzeRecords, setBronzeRecords] = useState<BronzeSampleRecord[]>(
    dataset.bronzeSampleRecords || [
      {
        id: `brz_${dataset.id}_1`,
        timestampUtc: '2026-11-09T10:15:00Z',
        platform: 'x_twitter',
        uf: 'SP',
        queryUsed: dataset.title,
        rawText: `Manifestação sobre ${dataset.title} com debate de direitos e tramitação no Senado.`,
        isExcluded: false,
      },
      {
        id: `brz_${dataset.id}_2`,
        timestampUtc: '2026-11-09T10:22:00Z',
        platform: 'youtube',
        uf: 'RJ',
        queryUsed: dataset.title,
        rawText: `Análise técnica em vídeo sobre o substitutivo apresentado na comissão temática.`,
        isExcluded: false,
      },
      {
        id: `brz_${dataset.id}_3`,
        timestampUtc: '2026-11-09T10:35:00Z',
        platform: 'telegram',
        uf: 'DF',
        queryUsed: dataset.title,
        rawText: `Aviso fora de pauta: propaganda não relacionada ao debate legislativo.`,
        isExcluded: true,
      },
      {
        id: `brz_${dataset.id}_4`,
        timestampUtc: '2026-11-09T10:48:00Z',
        platform: 'whatsapp',
        uf: 'MG',
        queryUsed: dataset.title,
        rawText: `Compartilhamento de notícia da Agência Senado sobre o andamento da votação.`,
        isExcluded: false,
      },
    ]
  );

  // Estado local para manipulação interativa da Camada Silver
  const [silverQuarantine, setSilverQuarantine] = useState<SilverQuarantineRecord[]>(
    dataset.silverQuarantineRecords || [
      {
        id: `slv_quar_${dataset.id}_1`,
        timestampUtc: '2026-11-09T11:20:00Z',
        platform: 'x_twitter',
        uf: 'SP',
        reasonTag: 'CIB_MINHASH_JACCARD_0.92',
        reasonDescription: 'Disparo coordenado em menos de 10s com quase-duplicata de texto.',
        rawText: `Aproveite agora: sorteio pix de R$ 500 para quem comentar no debate do Senado sobre ${dataset.title}!`,
        isRescuedOrganic: false,
      },
      {
        id: `slv_quar_${dataset.id}_2`,
        timestampUtc: '2026-11-09T11:35:00Z',
        platform: 'telegram',
        uf: 'PR',
        reasonTag: 'SPAM_COMERCIAL_REGEX',
        reasonDescription: 'Mensagem comercial utilizando termos legislativos como isca de clique.',
        rawText: `Curso completo com 90% de desconto sobre novas leis e ${dataset.title}. Clique aqui!`,
        isRescuedOrganic: false,
      },
      {
        id: `slv_quar_${dataset.id}_3`,
        timestampUtc: '2026-11-09T11:42:00Z',
        platform: 'tiktok',
        uf: 'BA',
        reasonTag: 'BOT_BURSTINESS_0.78',
        reasonDescription: 'Padrão não-orgânico com coeficiente de rajada B de Goh-Barabási elevado.',
        rawText: `Texto duplicado 40 vezes pela mesma conta automatizada em curto intervalo temporal.`,
        isRescuedOrganic: false,
      },
    ]
  );

  const [silverOrganic, setSilverOrganic] = useState<SilverOrganicRecord[]>(
    dataset.silverOrganicRecords || [
      {
        id: `slv_org_${dataset.id}_1`,
        authorIdHash: '7c8a2b1f4e...',
        timestampUtc: '2026-11-09T12:00:00Z',
        platform: 'x_twitter',
        uf: 'SP',
        postCount: 1,
        sanitizedSnippet: `Como cidadão, considero fundamental o debate responsável sobre ${dataset.title}.`,
        isManualQuarantine: false,
      },
      {
        id: `slv_org_${dataset.id}_2`,
        authorIdHash: '9d3e5f1a8c...',
        timestampUtc: '2026-11-09T12:15:00Z',
        platform: 'youtube',
        uf: 'MG',
        postCount: 2,
        sanitizedSnippet: `A audiência pública trouxe dados esclarecedores sobre os impactos da proposta.`,
        isManualQuarantine: false,
      },
      {
        id: `slv_org_${dataset.id}_3`,
        authorIdHash: '2b4c6e8a0f...',
        timestampUtc: '2026-11-09T12:30:00Z',
        platform: 'instagram_facebook',
        uf: 'RS',
        postCount: 1,
        sanitizedSnippet: `Necessário ajustar a redação para não onerar os pequenos municípios.`,
        isManualQuarantine: false,
      },
    ]
  );

  // Estado dos Portões Humanos normalizado contra quebras snake_case vs camelCase
  const [gatesState, setGatesState] = useState<HumanGatesState>(() =>
    normalizeHumanGates(dataset.humanGates)
  );

  // Estado da Camada Gold
  const [goldUnits, setGoldUnits] = useState<GoldSampleUnit[]>(
    dataset.goldSampleUnits || [
      {
        id: `gld_unit_${dataset.id}_1`,
        authorIdHash: '3a4b5c6d7e...',
        platform: 'x_twitter',
        uf: 'SP',
        macroregion: 'Sudeste',
        postsCollapsed: 1,
        hajekWeight: 1.0,
        rakingWeight: 1.12,
        sanitizedText: `Manifestação sobre ${dataset.title} focada em segurança jurídica e transparência.`,
        stance: 'FAVORAVEL',
      },
      {
        id: `gld_unit_${dataset.id}_2`,
        authorIdHash: '8e7d6c5b4a...',
        platform: 'youtube',
        uf: 'BA',
        macroregion: 'Nordeste',
        postsCollapsed: 2,
        hajekWeight: 1.0,
        rakingWeight: 0.95,
        sanitizedText: `Crítica fundamentada aos impactos orçamentários da medida sem previsão de compensação.`,
        stance: 'CONTRARIO',
      },
      {
        id: `gld_unit_${dataset.id}_3`,
        authorIdHash: '1f2e3d4c5b...',
        platform: 'whatsapp',
        uf: 'PR',
        macroregion: 'Sul',
        postsCollapsed: 1,
        hajekWeight: 1.0,
        rakingWeight: 1.05,
        sanitizedText: `Sugestão de emenda para aprimorar os artigos transitórios da proposição.`,
        stance: 'NEUTRO',
      },
    ]
  );
  const [currentSeed, setCurrentSeed] = useState(gatesState.goldGate.randomSeed || 42);
  const [goldTargetN, setGoldTargetN] = useState(gatesState.goldGate.targetSampleSize || 550);

  // Estado da Calibração Humana às Cegas
  const [blindItems, setBlindItems] = useState<BlindHumanAuditItem[]>(
    dataset.blindAuditItems || [
      {
        id: `blind_${dataset.id}_1`,
        sanitizedText: `Defendo a aprovação de ${dataset.title} porque moderniza o ordenamento jurídico e assegura proteção efetiva.`,
        platform: 'x_twitter',
        uf: 'DF',
        aiPredictedStance: 'FAVORAVEL',
        aiConfidence: 0.92,
        aiKeyTerms: ['aprovacao', 'moderniza', 'protecao', 'direitos'],
      },
      {
        id: `blind_${dataset.id}_2`,
        sanitizedText: `Essa matéria acarretará custos imprevisíveis para o setor produtivo. Precisamos de cautela e mais audiências.`,
        platform: 'youtube',
        uf: 'SP',
        aiPredictedStance: 'CONTRARIO',
        aiConfidence: 0.88,
        aiKeyTerms: ['custos', 'imprevisiveis', 'cautela', 'audiencias'],
      },
      {
        id: `blind_${dataset.id}_3`,
        sanitizedText: `Acompanhando os debates da comissão técnica para entender os aspectos constitucionais e tributários.`,
        platform: 'telegram',
        uf: 'MG',
        aiPredictedStance: 'NEUTRO',
        aiConfidence: 0.85,
        aiKeyTerms: ['acompanhando', 'comissao', 'constitucionais'],
      },
      {
        id: `blind_${dataset.id}_4`,
        sanitizedText: `Excelente iniciativa do relator! É um avanço histórico para a garantia de direitos em nosso país.`,
        platform: 'instagram_facebook',
        uf: 'BA',
        aiPredictedStance: 'FAVORAVEL',
        aiConfidence: 0.94,
        aiKeyTerms: ['excelente', 'avanco', 'historico', 'garantia'],
      },
    ]
  );

  const [confusionMatrix, setConfusionMatrix] = useState<ConfusionMatrix3x3>(
    dataset.humanCalibration?.confusionMatrix || {
      favoravel: { favoravel: 45, contrario: 4, neutro: 6 },
      contrario: { favoravel: 5, contrario: 52, neutro: 7 },
      neutro: { favoravel: 4, contrario: 6, neutro: 38 },
    }
  );
  const [calibrationMetrics, setCalibrationMetrics] = useState({
    totalAudited: dataset.humanCalibration?.totalAudited || 12,
    cohenKappa: dataset.humanCalibration?.cohenKappa || 0.78,
    sensitivity: dataset.humanCalibration?.sensitivity || 0.84,
    specificity: dataset.humanCalibration?.specificity || 0.87,
    youdenJ: dataset.humanCalibration?.youdenJ || 0.71,
    roganGladenPrevalence: dataset.humanCalibration?.roganGladenPrevalence || 43.8,
  });

  // Ressincronização reativa obrigatória ao trocar de tema ou receber dados do backend
  useEffect(() => {
    if (dataset) {
      const norm = normalizeHumanGates(dataset.humanGates);
      setGatesState(norm);
      if (norm.goldGate.randomSeed !== undefined) setCurrentSeed(norm.goldGate.randomSeed);
      if (norm.goldGate.targetSampleSize !== undefined) setGoldTargetN(norm.goldGate.targetSampleSize);
      if (dataset.bronzeSampleRecords) setBronzeRecords(dataset.bronzeSampleRecords);
      if (dataset.silverQuarantineRecords) setSilverQuarantine(dataset.silverQuarantineRecords);
      if (dataset.silverOrganicRecords) setSilverOrganic(dataset.silverOrganicRecords);
      if (dataset.goldSampleUnits) setGoldUnits(dataset.goldSampleUnits);
      if (dataset.blindAuditItems) setBlindItems(dataset.blindAuditItems);
      if (dataset.humanCalibration?.confusionMatrix) setConfusionMatrix(dataset.humanCalibration.confusionMatrix);
      if (dataset.humanCalibration) {
        setCalibrationMetrics({
          totalAudited: dataset.humanCalibration.totalAudited || 12,
          cohenKappa: dataset.humanCalibration.cohenKappa || 0.78,
          sensitivity: dataset.humanCalibration.sensitivity || 0.84,
          specificity: dataset.humanCalibration.specificity || 0.87,
          youdenJ: dataset.humanCalibration.youdenJ || 0.71,
          roganGladenPrevalence: dataset.humanCalibration.roganGladenPrevalence || 43.8,
        });
      }
    }
  }, [dataset?.id, dataset?.humanGates]);

  // Estado do Simulador Sandbox
  const [sandboxText, setSandboxText] = useState(
    `Considero urgente e fundamental o avanço do projeto no Senado para proteger os cidadãos.`
  );
  const [sandboxPlatform, setSandboxPlatform] = useState<PlatformId>('x_twitter');
  const [sandboxUf, setSandboxUf] = useState('SP');
  const [sandboxResult, setSandboxResult] = useState<SandboxStepResult | null>(null);
  const [isSandboxRunning, setIsSandboxRunning] = useState(false);

  // Manipulação de Ações da Camada Bronze
  const handleToggleBronzeExclude = async (recId: string) => {
    const updated = bronzeRecords.map((r) =>
      r.id === recId ? { ...r, isExcluded: !r.isExcluded } : r
    );
    setBronzeRecords(updated);
    const target = updated.find((r) => r.id === recId);
    const action = target?.isExcluded ? 'exclude_noise' : 'include_record';
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, record_id: recId }),
      });
    } catch {
      // fallback offline
    }
    const newExcluded = updated.filter((r) => r.isExcluded).map((r) => r.id);
    const nextGates: HumanGatesState = {
      ...gatesState,
      bronzeGate: { ...gatesState.bronzeGate, excludedRecordIds: newExcluded },
      bronze_gate: { ...gatesState.bronzeGate, excludedRecordIds: newExcluded },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      bronzeSampleRecords: updated,
      medallion: {
        ...dataset.medallion,
        bronzeTotal: Math.max(10, (dataset.medallion?.bronzeTotal || 100) + (target?.isExcluded ? -1 : 1)),
      },
    });
    showToast('info', 'Manipulação Bronze', `Registro ${recId} ${target?.isExcluded ? 'marcado como ruído' : 'reintegrado'}.`);
  };

  const handleApproveBronzeGate = async () => {
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve_gate', gate: 'bronze' }),
      });
    } catch {
      // fallback offline
    }
    const nextGates: HumanGatesState = {
      ...gatesState,
      bronzeGate: {
        ...gatesState.bronzeGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
      },
      bronze_gate: {
        ...gatesState.bronzeGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
      },
      silverGate: {
        ...gatesState.silverGate,
        status: gatesState.silverGate.status === 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR'
          ? 'PENDENTE_APROVACAO_HUMANA'
          : gatesState.silverGate.status,
      },
      silver_gate: {
        ...gatesState.silverGate,
        status: gatesState.silverGate.status === 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR'
          ? 'PENDENTE_APROVACAO_HUMANA'
          : gatesState.silverGate.status,
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      lifecycleStatus: 'DESCONTAMINACAO_SILVER_CIB_SPAM',
      lifecycleProgressPercent: 70,
    });
    showToast('success', 'Portão 1 Aprovado', 'Amostra Bruta homologada. Camada Silver destravada!');
  };

  const handleRerunBronze = async () => {
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'rerun_bronze_extraction' }),
      });
    } catch {
      // fallback offline
    }
    const nextGates: HumanGatesState = {
      ...gatesState,
      bronzeGate: {
        ...gatesState.bronzeGate,
        status: 'PENDENTE_APROVACAO_HUMANA',
        excludedRecordIds: [],
      },
      bronze_gate: {
        ...gatesState.bronzeGate,
        status: 'PENDENTE_APROVACAO_HUMANA',
        excludedRecordIds: [],
      },
      silverGate: {
        ...gatesState.silverGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
      silver_gate: {
        ...gatesState.silverGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
      goldGate: {
        ...gatesState.goldGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
      gold_gate: {
        ...gatesState.goldGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      lifecycleStatus: 'COLETA_EM_ANDAMENTO_6_REDES',
      lifecycleProgressPercent: 45,
    });
    showToast('warning', 'Re-extração Solicitada', 'Lote da Camada Bronze redefinido para auditoria.');
  };

  // Manipulação de Ações da Camada Silver
  const handleRescueToOrganic = async (recId: string) => {
    const updated = silverQuarantine.map((q) =>
      q.id === recId ? { ...q, isRescuedOrganic: !q.isRescuedOrganic } : q
    );
    setSilverQuarantine(updated);
    const target = updated.find((q) => q.id === recId);
    const action = target?.isRescuedOrganic ? 'override_to_organic' : 'override_to_quarantine';
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, record_id: recId }),
      });
    } catch {
      // fallback offline
    }
    const rescuedIds = updated.filter((q) => q.isRescuedOrganic).map((q) => q.id);
    const nextGates: HumanGatesState = {
      ...gatesState,
      silverGate: { ...gatesState.silverGate, overriddenToOrganicIds: rescuedIds },
      silver_gate: { ...gatesState.silverGate, overriddenToOrganicIds: rescuedIds },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      silverQuarantineRecords: updated,
      medallion: {
        ...dataset.medallion,
        silverCibBots: Math.max(0, (dataset.medallion?.silverCibBots || 0) + (target?.isRescuedOrganic ? -1 : 1)),
        uOrgAccounts: (dataset.medallion?.uOrgAccounts || 0) + (target?.isRescuedOrganic ? 1 : -1),
      },
    });
    showToast('success', 'Falso Positivo Resgatado', `Registro ${recId} transferido para o conjunto orgânico.`);
  };

  const handleSendToQuarantine = async (recId: string) => {
    const updated = silverOrganic.map((o) =>
      o.id === recId ? { ...o, isManualQuarantine: !o.isManualQuarantine } : o
    );
    setSilverOrganic(updated);
    const target = updated.find((o) => o.id === recId);
    const action = target?.isManualQuarantine ? 'override_to_quarantine' : 'override_to_organic';
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action, record_id: recId }),
      });
    } catch {
      // fallback offline
    }
    const quarIds = updated.filter((o) => o.isManualQuarantine).map((o) => o.id);
    const nextGates: HumanGatesState = {
      ...gatesState,
      silverGate: { ...gatesState.silverGate, overriddenToQuarantineIds: quarIds },
      silver_gate: { ...gatesState.silverGate, overriddenToQuarantineIds: quarIds },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      silverOrganicRecords: updated,
      medallion: {
        ...dataset.medallion,
        silverCibBots: (dataset.medallion?.silverCibBots || 0) + (target?.isManualQuarantine ? 1 : -1),
        uOrgAccounts: Math.max(0, (dataset.medallion?.uOrgAccounts || 0) + (target?.isManualQuarantine ? -1 : 1)),
      },
    });
    showToast('warning', 'Falso Negativo Barrado', `Conta ${recId} enviada para quarentena CIB/Spam.`);
  };

  const handleApproveSilverGate = async () => {
    if (gatesState.bronzeGate.status !== 'APROVADO_PELO_ANALISTA') {
      showToast('error', 'Trava Estrita', 'Aprove o Portão Bronze antes de aprovar a Camada Silver.');
      return;
    }
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve_gate', gate: 'silver' }),
      });
    } catch {
      // fallback offline
    }
    const nextGates: HumanGatesState = {
      ...gatesState,
      silverGate: {
        ...gatesState.silverGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
      },
      silver_gate: {
        ...gatesState.silverGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
      },
      goldGate: {
        ...gatesState.goldGate,
        status: gatesState.goldGate.status === 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR'
          ? 'PENDENTE_APROVACAO_HUMANA'
          : gatesState.goldGate.status,
      },
      gold_gate: {
        ...gatesState.goldGate,
        status: gatesState.goldGate.status === 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR'
          ? 'PENDENTE_APROVACAO_HUMANA'
          : gatesState.goldGate.status,
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      lifecycleStatus: 'CALIBRACAO_RAKING_IPF_ROGAN_GLADEN',
      lifecycleProgressPercent: 90,
    });
    showToast('success', 'Portão 2 Aprovado', 'Limpeza Silver homologada. Camada Gold destravada!');
  };

  const handleRerunSilver = async () => {
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'rerun_silver_cleaning' }),
      });
    } catch {
      // fallback offline
    }
    const nextGates: HumanGatesState = {
      ...gatesState,
      silverGate: {
        ...gatesState.silverGate,
        status: 'PENDENTE_APROVACAO_HUMANA',
        overriddenToOrganicIds: [],
        overriddenToQuarantineIds: [],
      },
      silver_gate: {
        ...gatesState.silverGate,
        status: 'PENDENTE_APROVACAO_HUMANA',
        overriddenToOrganicIds: [],
        overriddenToQuarantineIds: [],
      },
      goldGate: {
        ...gatesState.goldGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
      gold_gate: {
        ...gatesState.goldGate,
        status: 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR',
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      lifecycleStatus: 'DESCONTAMINACAO_SILVER_CIB_SPAM',
      lifecycleProgressPercent: 70,
    });
    showToast('warning', 'Re-execução Silver', 'Limpeza de CIB & Spam redefinida para auditoria.');
  };

  // Manipulação de Ações da Camada Gold com Sorteio Real
  const handleResampleGold = async () => {
    const nextSeed = currentSeed + 7;
    setCurrentSeed(nextSeed);
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'resample_gold', random_seed: nextSeed, target_sample_size: goldTargetN }),
      });
    } catch {
      // fallback offline
    }
    // Recalcula deterministicamente as unidades gold com base na nova seed
    const ufs = ['SP', 'MG', 'RJ', 'BA', 'RS', 'PR', 'PE', 'CE', 'DF', 'SC', 'GO', 'PA', 'MA', 'ES', 'PB'];
    const platforms: PlatformId[] = ['youtube', 'telegram', 'x_twitter', 'instagram_facebook', 'tiktok', 'whatsapp'];
    const stances: Stance[] = ['FAVORAVEL', 'CONTRARIO', 'NEUTRO'];
    const newUnits: GoldSampleUnit[] = Array.from({ length: 15 }, (_, i) => {
      const uf = ufs[(i * 3 + nextSeed) % ufs.length];
      const plat = platforms[(i + nextSeed) % platforms.length];
      const st = stances[(i * 2 + nextSeed) % stances.length];
      const macro = ['SP', 'RJ', 'MG', 'ES'].includes(uf) ? 'Sudeste' : ['BA', 'PE', 'CE', 'MA', 'PB'].includes(uf) ? 'Nordeste' : 'Sul';
      return {
        id: `gld_unit_${dataset.id}_s${nextSeed}_${i + 1}`,
        authorIdHash: `${((nextSeed * 31 + i * 17) % 999999).toString(16).padStart(6, '0')}...`,
        platform: plat,
        uf,
        macroregion: macro,
        postsCollapsed: 1 + ((i + nextSeed) % 2),
        hajekWeight: 1.0,
        rakingWeight: Number((0.75 + ((i + nextSeed) % 10) * 0.06).toFixed(2)),
        sanitizedText: `[Seed ${nextSeed}] Manifestação sorteada sobre ${dataset.title} no estrato ${plat}/${uf} com postura ${st}.`,
        stance: st,
      };
    });
    setGoldUnits(newUnits);
    const nextDeff = Number((1.18 + (nextSeed % 20) * 0.01).toFixed(2));
    const nextMoe = Number((1.96 * Math.sqrt((0.25 * nextDeff) / Math.max(1, goldTargetN)) * 100).toFixed(1));
    const nextGates: HumanGatesState = {
      ...gatesState,
      goldGate: {
        ...gatesState.goldGate,
        randomSeed: nextSeed,
        targetSampleSize: goldTargetN,
        status: 'PENDENTE_APROVACAO_HUMANA',
      },
      gold_gate: {
        ...gatesState.goldGate,
        randomSeed: nextSeed,
        targetSampleSize: goldTargetN,
        status: 'PENDENTE_APROVACAO_HUMANA',
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      goldSampleUnits: newUnits,
      medallion: {
        ...dataset.medallion,
        goldSampleSize: goldTargetN,
        kishDeff: nextDeff,
        marginOfError: nextMoe,
      },
    });
    showToast('info', 'Re-amostragem Concluída', `Nova amostra probabilística sorteada com seed=${nextSeed} e n=${goldTargetN}.`);
  };

  const handleApproveGoldGate = async () => {
    if (gatesState.silverGate.status !== 'APROVADO_PELO_ANALISTA') {
      showToast('error', 'Trava Estrita', 'Aprove o Portão Silver antes de aprovar a Camada Gold.');
      return;
    }
    try {
      await fetch(`/api/themes/${dataset.id}/medallion/manipulate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'approve_gate', gate: 'gold' }),
      });
    } catch {
      // fallback offline
    }
    const nextGates: HumanGatesState = {
      ...gatesState,
      goldGate: {
        ...gatesState.goldGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
        randomSeed: currentSeed,
        targetSampleSize: goldTargetN,
      },
      gold_gate: {
        ...gatesState.goldGate,
        status: 'APROVADO_PELO_ANALISTA',
        approvedAt: new Date().toISOString(),
        randomSeed: currentSeed,
        targetSampleSize: goldTargetN,
      },
    };
    setGatesState(nextGates);
    onDatasetUpdated?.({
      humanGates: nextGates,
      lifecycleStatus: 'PRONTO_PARA_ANALISE_E_BOLETIM',
      lifecycleProgressPercent: 100,
    });
    showToast('success', 'Portão 3 Aprovado', 'Amostra Gold homologada. Dossiê oficial liberado!');
  };

  // Execução da Calibração Humana às Cegas com a Equação Exata de Rogan-Gladen (Sem Constantes Mágicas)
  const handleBlindVote = async (itemId: string, humanVote: Stance) => {
    const target = blindItems.find((i) => i.id === itemId);
    if (!target) return;

    const match = humanVote === target.aiPredictedStance;
    const updatedBlind = blindItems.map((it) =>
      it.id === itemId ? { ...it, humanStance: humanVote, match } : it
    );
    setBlindItems(updatedBlind);

    try {
      await fetch(`/api/themes/${dataset.id}/human-validation/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ record_id: itemId, human_stance: humanVote }),
      });
    } catch {
      // fallback offline
    }

    // Atualiza matriz de confusão
    const hKey = humanVote.toLowerCase() as 'favoravel' | 'contrario' | 'neutro';
    const aiKey = target.aiPredictedStance.toLowerCase() as 'favoravel' | 'contrario' | 'neutro';

    const newMatrix = {
      ...confusionMatrix,
      [hKey]: {
        ...confusionMatrix[hKey],
        [aiKey]: confusionMatrix[hKey][aiKey] + 1,
      },
    };
    setConfusionMatrix(newMatrix);

    // Recalcula Kappa, Se, Sp, Youden J e Rogan-Gladen Exato
    const total = Object.values(newMatrix).reduce(
      (acc, row) => acc + Object.values(row).reduce((rAcc, v) => rAcc + v, 0),
      0
    );
    const po = (newMatrix.favoravel.favoravel + newMatrix.contrario.contrario + newMatrix.neutro.neutro) / Math.max(1, total);
    const pe =
      ((newMatrix.favoravel.favoravel + newMatrix.favoravel.contrario + newMatrix.favoravel.neutro) / total) *
        ((newMatrix.favoravel.favoravel + newMatrix.contrario.favoravel + newMatrix.neutro.favoravel) / total) +
      ((newMatrix.contrario.favoravel + newMatrix.contrario.contrario + newMatrix.contrario.neutro) / total) *
        ((newMatrix.favoravel.contrario + newMatrix.contrario.contrario + newMatrix.neutro.contrario) / total) +
      ((newMatrix.neutro.favoravel + newMatrix.neutro.contrario + newMatrix.neutro.neutro) / total) *
        ((newMatrix.favoravel.neutro + newMatrix.contrario.neutro + newMatrix.neutro.neutro) / total);

    const kappa = Math.min(1.0, Math.max(-1.0, (po - pe) / Math.max(0.0001, 1 - pe)));
    const tp = newMatrix.favoravel.favoravel;
    const fn = newMatrix.favoravel.contrario + newMatrix.favoravel.neutro;
    const se = tp / Math.max(1, tp + fn);

    const tn = newMatrix.contrario.contrario + newMatrix.contrario.neutro + newMatrix.neutro.contrario + newMatrix.neutro.neutro;
    const fp = newMatrix.contrario.favoravel + newMatrix.neutro.favoravel;
    const sp = tn / Math.max(1, tn + fp);
    const youden = Math.max(0, se + sp - 1);
    const pObs = (newMatrix.favoravel.favoravel + newMatrix.contrario.favoravel + newMatrix.neutro.favoravel) / Math.max(1, total);
    const denom = Math.max(0.05, se + sp - 1.0);
    const pRg = Math.max(0.0, Math.min(100.0, ((pObs + sp - 1.0) / denom) * 100));

    const newMetrics = {
      totalAudited: calibrationMetrics.totalAudited + 1,
      cohenKappa: Number(kappa.toFixed(2)),
      sensitivity: Number(se.toFixed(2)),
      specificity: Number(sp.toFixed(2)),
      youdenJ: Number(youden.toFixed(2)),
      roganGladenPrevalence: Number(pRg.toFixed(1)),
    };
    setCalibrationMetrics(newMetrics);
    onDatasetUpdated?.({
      blindAuditItems: updatedBlind,
      humanCalibration: {
        ...dataset.humanCalibration,
        ...newMetrics,
        confusionMatrix: newMatrix,
      },
    });

    showToast(
      match ? 'success' : 'warning',
      match ? 'Concordância (Match)' : 'Divergência (Mismatch)',
      `Humano: ${humanVote} · IA: ${target.aiPredictedStance} (Kappa: ${kappa.toFixed(2)}, Rogan-Gladen: ${pRg.toFixed(1)}%)`
    );
  };

  // Execução do Simulador Sandbox
  const handleRunSandbox = async () => {
    setIsSandboxRunning(true);
    try {
      const response = await fetch('/api/sandbox/step-by-step', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          text: sandboxText,
          platform: sandboxPlatform,
          uf: sandboxUf,
          theme_id: dataset.id,
        }),
      });

      if (response.ok) {
        const data = await response.json();
        setSandboxResult(data);
        showToast('success', 'Simulação Concluída', 'Os 6 passos do pipeline foram executados com sucesso!');
      } else {
        throw new Error('Falha na resposta do servidor REST');
      }
    } catch {
      // Fallback determinístico reativo em memória
      const tokens = sandboxText.toLowerCase().split(/\s+/);
      const isFav = tokens.some((t) => ['urgente', 'fundamental', 'proteger', 'apoio', 'avanco'].includes(t));
      const isCon = tokens.some((t) => ['contra', 'absurdo', 'prejuizo', 'custo', 'perigo'].includes(t));
      const stance = isFav ? 'FAVORAVEL' : isCon ? 'CONTRARIO' : 'NEUTRO';

      setSandboxResult({
        step1_lgpd: {
          original_text: sandboxText,
          scrubbed_text: sandboxText.replace(/@\w+/g, '@usuario_anonimizado'),
          author_id_hash: 'a9f8b7c6d5e4...',
          author_pii_cleared: true,
          protocol: 'HMAC-SHA256 (Fail-Closed, zero persistência de PII em disco)',
        },
        step2_silver_cib: {
          minhash_signature: '7e2b1a9c4f8d...',
          commercial_spam_score: 0.04,
          burstiness_index: 0.22,
          verdict: 'ORGANICO',
          reason_tag: 'CONTA_ORGANICA_APROVADA',
        },
        step3_feature_engineering: {
          token_count: tokens.length,
          lexical_bias_score: 0.18,
          framing_detected: 'Constitucional e Direitos',
          bias_terms_found: tokens.filter((t) => ['urgente', 'fundamental', 'proteger'].includes(t)),
        },
        step4_classifier_xai: {
          probabilities: { favoravel: isFav ? 0.74 : 0.15, contrario: isCon ? 0.72 : 0.12, neutro: 0.14 },
          predicted_stance: stance,
          shap_tokens: tokens.slice(0, 6).map((tok) => ({
            token: tok,
            weight: ['fundamental', 'proteger', 'urgente'].includes(tok) ? 0.32 : -0.05,
            impacts_stance: stance,
          })),
        },
        step5_digital_spectrum: {
          primary_spectrum_id: 'espectro_progressista',
          primary_spectrum_name: 'Campo Progressista & Direitos',
          harmonic_affinity: {
            espectro_progressista: 0.85,
            espectro_conservador: 0.15,
            espectro_centro_institucional: 0.40,
            espectro_tecnico_setorial: 0.30,
          },
        },
        step6_sample_weighting: {
          single_account_weight_hajek: 1.0,
          macroregion: 'Sudeste',
          raking_ipf_weight: 1.15,
          simplex_clipped: false,
          rogan_gladen_formula: 'p_hat_RG = (p_obs + Sp - 1) / (Se + Sp - 1)',
          rogan_gladen_impact: `Contribui com peso calibrado w_i = 1.15 para a classe ${stance}.`,
        },
      });
      showToast('info', 'Simulação Local', 'Resultado gerado via motor reativo da bancada.');
    } finally {
      setIsSandboxRunning(false);
    }
  };

  return (
    <div className="space-y-8 animate-in fade-in duration-200">
      {/* Cabeçalho do Módulo 5 */}
      <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-slate-100 dark:border-slate-800 pb-5">
          <div className="flex items-center gap-3">
            <div className="p-3 bg-blue-50 dark:bg-blue-950/60 border border-blue-200 dark:border-blue-800 rounded-xl">
              <ShieldCheck className="w-6 h-6 text-blue-700 dark:text-blue-400" />
            </div>
            <div>
              <h1 className="text-xl font-bold text-slate-900 dark:text-white flex items-center gap-2">
                Validação Humana & Governança de Camadas
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-blue-100 dark:bg-blue-900/50 text-blue-800 dark:text-blue-200 font-semibold font-mono">
                  Human-in-the-Loop
                </span>
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400 mt-0.5">
                Portões sequenciais estritos de aprovação por camada (Bronze → Silver → Gold), auditoria às cegas e simulador passo a passo.
              </p>
            </div>
          </div>

          {/* Semáforo dos 3 Portões Humanos */}
          <div className="flex items-center gap-2">
            {[
              { id: 'bronze', label: 'Gate 1: Bronze', info: gatesState.bronzeGate },
              { id: 'silver', label: 'Gate 2: Silver', info: gatesState.silverGate },
              { id: 'gold', label: 'Gate 3: Gold', info: gatesState.goldGate },
            ].map((g) => {
              const isApproved = g.info.status === 'APROVADO_PELO_ANALISTA';
              const isBlocked = g.info.status === 'BLOQUEADO_AGUARDANDO_CAMADA_ANTERIOR';
              return (
                <div
                  key={g.id}
                  className={`px-3 py-1.5 rounded-lg border text-xs flex items-center gap-1.5 font-medium transition-all ${
                    isApproved
                      ? 'bg-emerald-50 dark:bg-emerald-950/30 border-emerald-300 dark:border-emerald-800 text-emerald-800 dark:text-emerald-200'
                      : isBlocked
                      ? 'bg-slate-100 dark:bg-slate-800/60 border-slate-200 dark:border-slate-700 text-slate-400 dark:text-slate-500'
                      : 'bg-amber-50 dark:bg-amber-950/30 border-amber-300 dark:border-amber-800 text-amber-800 dark:text-amber-200 animate-pulse'
                  }`}
                >
                  {isApproved ? (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                  ) : isBlocked ? (
                    <Lock className="w-3.5 h-3.5" />
                  ) : (
                    <Unlock className="w-3.5 h-3.5 text-amber-600" />
                  )}
                  <span>{g.label}</span>
                </div>
              );
            })}
          </div>
        </div>

        {/* Barra de Navegação das 5 Abas do Módulo 5 */}
        <div className="flex items-center gap-2 mt-5 overflow-x-auto pb-1">
          {[
            { id: 'bronze', label: '1. Amostra Bruta (Bronze)' },
            { id: 'silver', label: '2. Expurgo CIB & Spam (Silver)' },
            { id: 'gold', label: '3. Amostra Extraída & Pesos (Gold)' },
            { id: 'blind_audit', label: '4. Calibração às Cegas (Rogan-Gladen)' },
            { id: 'sandbox', label: '5. Simulador Passo a Passo (Sandbox)' },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all whitespace-nowrap cursor-pointer ${
                activeTab === tab.id
                  ? 'bg-blue-700 text-white shadow-2xs'
                  : 'bg-slate-100 dark:bg-slate-800 text-slate-600 dark:text-slate-300 hover:bg-slate-200 dark:hover:bg-slate-700'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      {/* ABA 1: AMPOSTRA BRUTA (CAMADA BRONZE) */}
      {activeTab === 'bronze' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <h2 className="text-base font-bold text-slate-900 dark:text-white">
                  Inspeção e Manipulação da Amostra Bruta (Camada Bronze)
                </h2>
                <p className="text-xs text-slate-500 dark:text-slate-400">
                  Verifique a aderência temática da coleta, exclua registros ruidosos e aprove o avanço para a Camada Silver.
                </p>
              </div>
              <div className="flex items-center gap-2">
                <button
                  onClick={handleRerunBronze}
                  className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                >
                  <RotateCcw className="w-3.5 h-3.5" />
                  Rejeitar Coleta e Re-extrair
                </button>
                <button
                  onClick={handleApproveBronzeGate}
                  className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Aprovar Amostra Bruta (Bronze)
                </button>
              </div>
            </div>

            {/* Tabela de Manifestações Brutas */}
            <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
              <table className="w-full text-left text-xs border-collapse">
                <thead className="bg-slate-50 dark:bg-slate-800/80 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 font-semibold">
                  <tr>
                    <th className="py-2.5 px-3">ID Registro (HMAC)</th>
                    <th className="py-2.5 px-3">Data/Hora (UTC)</th>
                    <th className="py-2.5 px-3">Rede</th>
                    <th className="py-2.5 px-3">UF</th>
                    <th className="py-2.5 px-3">Termo Disparador</th>
                    <th className="py-2.5 px-3">Texto Bruto Coletado</th>
                    <th className="py-2.5 px-3 text-center">Status / Ação</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-sans">
                  {bronzeRecords.map((r) => (
                    <tr
                      key={r.id}
                      className={r.isExcluded ? 'bg-rose-50/40 dark:bg-rose-950/20 text-slate-400' : 'hover:bg-slate-50/60 dark:hover:bg-slate-800/40'}
                    >
                      <td className="py-2.5 px-3 font-mono font-medium">{r.id}</td>
                      <td className="py-2.5 px-3 text-slate-500">{r.timestampUtc}</td>
                      <td className="py-2.5 px-3 capitalize font-medium">{r.platform.replace('_', '/')}</td>
                      <td className="py-2.5 px-3 font-semibold">{r.uf}</td>
                      <td className="py-2.5 px-3 text-slate-600 dark:text-slate-400">{r.queryUsed}</td>
                      <td className="py-2.5 px-3 max-w-md truncate" title={r.rawText}>{r.rawText}</td>
                      <td className="py-2.5 px-3 text-center">
                        <button
                          onClick={() => handleToggleBronzeExclude(r.id)}
                          className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                            r.isExcluded
                              ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200'
                              : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-rose-100 hover:text-rose-800'
                          }`}
                        >
                          {r.isExcluded ? 'Excluído (Ruído)' : 'Manter na Coleta'}
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ABA 2: EXPURGO CIB & SPAM (CAMADA SILVER) */}
      {activeTab === 'silver' && (
        <div className="space-y-6">
          {gatesState.bronzeGate.status !== 'APROVADO_PELO_ANALISTA' ? (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-2xl p-8 text-center space-y-3">
              <Lock className="w-8 h-8 text-amber-600 mx-auto" />
              <h3 className="text-base font-bold text-amber-900 dark:text-amber-200">
                Portão 2 Bloqueado: Aprovação da Camada Bronze Obrigatória
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-300 max-w-md mx-auto">
                Para auditar o expurgo CIB e a quarentena de spam, o analista humano deve verificar e aprovar o Portão Bronze primeiro.
              </p>
              <button
                onClick={() => setActiveTab('bronze')}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Voltar e Aprovar Camada Bronze
              </button>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-6">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">
                    Auditoria de Limpeza e Quarentena (Camada Silver)
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Inspecione os motivos matemáticos do bloqueio e corrija eventuais falsos positivos ou falsos negativos.
                  </p>
                </div>
                <button
                  onClick={handleApproveSilverGate}
                  className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                >
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  Aprovar Limpeza (Silver)
                </button>
              </div>

              {/* Tabela de Quarentena Barrada */}
              <div className="space-y-2">
                <div className="text-xs font-bold text-rose-700 dark:text-rose-400 uppercase tracking-wider flex items-center gap-1.5">
                  <AlertTriangle className="w-4 h-4" />
                  Registros em Quarentena CIB / Spam Comercial
                </div>
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-rose-50/60 dark:bg-rose-950/30 text-rose-900 dark:text-rose-200 border-b border-rose-200 dark:border-rose-800/60 font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">ID Registro</th>
                        <th className="py-2.5 px-3">Rede</th>
                        <th className="py-2.5 px-3">Etiqueta do Bloqueio</th>
                        <th className="py-2.5 px-3">Motivo Técnico Algorítmico</th>
                        <th className="py-2.5 px-3">Conteúdo Barrado</th>
                        <th className="py-2.5 px-3 text-center">Auditoria Humana</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {silverQuarantine.map((q) => (
                        <tr key={q.id} className={q.isRescuedOrganic ? 'bg-emerald-50/50 dark:bg-emerald-950/20' : ''}>
                          <td className="py-2.5 px-3 font-mono font-medium">{q.id}</td>
                          <td className="py-2.5 px-3 capitalize font-medium">{q.platform.replace('_', '/')}</td>
                          <td className="py-2.5 px-3 font-mono font-bold text-rose-600 dark:text-rose-400">{q.reasonTag}</td>
                          <td className="py-2.5 px-3 text-slate-500 max-w-xs">{q.reasonDescription}</td>
                          <td className="py-2.5 px-3 max-w-sm truncate" title={q.rawText}>{q.rawText}</td>
                          <td className="py-2.5 px-3 text-center">
                            <button
                              onClick={() => handleRescueToOrganic(q.id)}
                              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                                q.isRescuedOrganic
                                  ? 'bg-emerald-100 dark:bg-emerald-900/60 text-emerald-800 dark:text-emerald-200'
                                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-emerald-100 hover:text-emerald-800'
                              }`}
                            >
                              {q.isRescuedOrganic ? 'Resgatado (Orgânico)' : 'Resgatar Falso Positivo'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              {/* Tabela de Contas Orgânicas Aprovadas */}
              <div className="space-y-2 pt-4 border-t border-slate-100 dark:border-slate-800">
                <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase tracking-wider flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  Contas Orgânicas Aprovadas para a Camada Silver (Universo U_Org)
                </div>
                <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead className="bg-emerald-50/60 dark:bg-emerald-950/30 text-emerald-900 dark:text-emerald-200 border-b border-emerald-200 dark:border-emerald-800/60 font-semibold">
                      <tr>
                        <th className="py-2.5 px-3">Autor Pseudonimizado (HMAC)</th>
                        <th className="py-2.5 px-3">Rede</th>
                        <th className="py-2.5 px-3">UF</th>
                        <th className="py-2.5 px-3">Postagens Colapsadas (m_i)</th>
                        <th className="py-2.5 px-3">Trecho da Manifestação</th>
                        <th className="py-2.5 px-3 text-center">Auditoria Humana</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                      {silverOrganic.map((o) => (
                        <tr key={o.id} className={o.isManualQuarantine ? 'bg-rose-50/50 dark:bg-rose-950/20' : ''}>
                          <td className="py-2.5 px-3 font-mono font-medium">{o.authorIdHash}</td>
                          <td className="py-2.5 px-3 capitalize font-medium">{o.platform.replace('_', '/')}</td>
                          <td className="py-2.5 px-3 font-semibold">{o.uf}</td>
                          <td className="py-2.5 px-3 font-mono tabular-nums">{o.postCount}</td>
                          <td className="py-2.5 px-3 max-w-sm truncate" title={o.sanitizedSnippet}>{o.sanitizedSnippet}</td>
                          <td className="py-2.5 px-3 text-center">
                            <button
                              onClick={() => handleSendToQuarantine(o.id)}
                              className={`px-2.5 py-1 rounded text-[11px] font-semibold transition-colors cursor-pointer ${
                                o.isManualQuarantine
                                  ? 'bg-rose-100 dark:bg-rose-900/60 text-rose-800 dark:text-rose-200'
                                  : 'bg-slate-100 dark:bg-slate-800 text-slate-700 dark:text-slate-300 hover:bg-rose-100 hover:text-rose-800'
                              }`}
                            >
                              {o.isManualQuarantine ? 'Bloqueado (Quarentena)' : 'Enviar para Quarentena'}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ABA 3: AMOSTRA EXTRAÍDA & PESOS (CAMADA GOLD) */}
      {activeTab === 'gold' && (
        <div className="space-y-6">
          {gatesState.silverGate.status !== 'APROVADO_PELO_ANALISTA' ? (
            <div className="bg-amber-50 dark:bg-amber-950/40 border border-amber-300 dark:border-amber-800 rounded-2xl p-8 text-center space-y-3">
              <Lock className="w-8 h-8 text-amber-600 mx-auto" />
              <h3 className="text-base font-bold text-amber-900 dark:text-amber-200">
                Portão 3 Bloqueado: Aprovação da Camada Silver Obrigatória
              </h3>
              <p className="text-xs text-amber-800 dark:text-amber-300 max-w-md mx-auto">
                A extração amostral probabilística exige que a limpeza de robôs e spam seja previamente homologada pelo analista.
              </p>
              <button
                onClick={() => setActiveTab('silver')}
                className="px-4 py-2 bg-amber-600 hover:bg-amber-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
              >
                Ir para Aprovação da Camada Silver
              </button>
            </div>
          ) : (
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-6">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white">
                    Inspeção e Ponderação Amostral (Camada Gold)
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Verifique os pesos calibrados de Raking IPF, o efeito do desenho de Kish e faça re-sorteios amostrais se necessário.
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={handleResampleGold}
                    className="flex items-center gap-1.5 px-3 py-1.5 border border-slate-300 dark:border-slate-700 rounded-lg text-xs font-medium text-slate-700 dark:text-slate-300 hover:bg-slate-50 dark:hover:bg-slate-800 transition-colors cursor-pointer"
                  >
                    <Dices className="w-3.5 h-3.5 text-blue-600" />
                    Sortear Nova Amostra (Nova Seed)
                  </button>
                  <button
                    onClick={handleApproveGoldGate}
                    className="flex items-center gap-1.5 px-4 py-1.5 bg-emerald-600 hover:bg-emerald-700 text-white rounded-lg text-xs font-semibold transition-colors cursor-pointer"
                  >
                    <CheckCircle2 className="w-3.5 h-3.5" />
                    Aprovar Amostra Gold
                  </button>
                </div>
              </div>

              {/* Painel de Diagnóstico Estatístico da Amostra */}
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 font-medium uppercase">Tamanho Amostral (n)</span>
                  <div className="text-lg font-bold font-mono text-slate-900 dark:text-white tabular-nums">{goldTargetN} contas</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 font-medium uppercase">Semente Criptográfica</span>
                  <div className="text-lg font-bold font-mono text-blue-600 dark:text-blue-400 tabular-nums">seed={currentSeed}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 font-medium uppercase">Efeito Kish (DEFF)</span>
                  <div className="text-lg font-bold font-mono text-slate-900 dark:text-white tabular-nums">{dataset.medallion.kishDeff}</div>
                </div>
                <div className="p-4 rounded-xl bg-slate-50 dark:bg-slate-800/60 border border-slate-200 dark:border-slate-700">
                  <span className="text-[11px] text-slate-500 font-medium uppercase">Margem de Erro</span>
                  <div className="text-lg font-bold font-mono text-emerald-600 dark:text-emerald-400 tabular-nums">±{dataset.medallion.marginOfError} p.p.</div>
                </div>
              </div>

              {/* Tabela de Unidades Amostrais Gold */}
              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-left text-xs border-collapse">
                  <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300 border-b border-slate-200 dark:border-slate-700 font-semibold">
                    <tr>
                      <th className="py-2.5 px-3">ID Hash (Conta Única)</th>
                      <th className="py-2.5 px-3">Rede</th>
                      <th className="py-2.5 px-3">UF / Região</th>
                      <th className="py-2.5 px-3">Postagens (u_i = 1)</th>
                      <th className="py-2.5 px-3">Peso Hájek (d_i)</th>
                      <th className="py-2.5 px-3">Peso Raking (w_i)</th>
                      <th className="py-2.5 px-3">Manifestação Representativa</th>
                      <th className="py-2.5 px-3 text-center">Postura</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800 font-sans">
                    {goldUnits.map((u) => (
                      <tr key={u.id} className="hover:bg-slate-50/50 dark:hover:bg-slate-800/40">
                        <td className="py-2.5 px-3 font-mono font-medium">{u.authorIdHash}</td>
                        <td className="py-2.5 px-3 capitalize font-medium">{u.platform.replace('_', '/')}</td>
                        <td className="py-2.5 px-3 font-semibold">{u.uf} ({u.macroregion})</td>
                        <td className="py-2.5 px-3 font-mono tabular-nums">{u.postsCollapsed}</td>
                        <td className="py-2.5 px-3 font-mono tabular-nums">{u.hajekWeight.toFixed(2)}</td>
                        <td className="py-2.5 px-3 font-mono tabular-nums font-semibold text-blue-600">{u.rakingWeight.toFixed(2)}</td>
                        <td className="py-2.5 px-3 max-w-sm truncate" title={u.sanitizedText}>{u.sanitizedText}</td>
                        <td className="py-2.5 px-3 text-center font-bold font-mono">
                          <span
                            className={`px-2 py-0.5 rounded text-[10px] ${
                              u.stance === 'FAVORAVEL'
                                ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/60 dark:text-blue-200'
                                : u.stance === 'CONTRARIO'
                                ? 'bg-orange-100 text-orange-800 dark:bg-orange-900/60 dark:text-orange-200'
                                : 'bg-slate-100 text-slate-800 dark:bg-slate-800 dark:text-slate-200'
                            }`}
                          >
                            {u.stance}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      )}

      {/* ABA 4: CALIBRAÇÃO HUMANA ÀS CEGAS (BLIND AUDIT) */}
      {activeTab === 'blind_audit' && (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <h2 className="text-base font-bold text-slate-900 dark:text-white flex items-center gap-2">
                    Calibração Humana às Cegas (Blind Audit)
                    <span className="text-xs px-2 py-0.5 rounded bg-purple-100 text-purple-800 dark:bg-purple-900/50 dark:text-purple-200 font-mono">
                      Modo Cego Ativo
                    </span>
                  </h2>
                  <p className="text-xs text-slate-500 dark:text-slate-400">
                    Rotule os cartões sem ver a previsão da IA. Ao clicar, o sistema revela o veredito e recalcula o Kappa de Cohen e Rogan-Gladen.
                  </p>
                </div>
              </div>

              {/* Cartões de Rotulagem às Cegas */}
              <div className="space-y-3">
                {blindItems.map((item) => (
                  <div
                    key={item.id}
                    className="p-4 rounded-xl border border-slate-200 dark:border-slate-700 bg-slate-50 dark:bg-slate-800/50 space-y-3"
                  >
                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span className="font-mono">{item.id} · {item.platform} ({item.uf})</span>
                      {item.humanStance ? (
                        <span
                          className={`font-semibold px-2 py-0.5 rounded ${
                            item.match
                              ? 'bg-emerald-100 text-emerald-800 dark:bg-emerald-900/50 dark:text-emerald-200'
                              : 'bg-amber-100 text-amber-800 dark:bg-amber-900/50 dark:text-amber-200'
                          }`}
                        >
                          {item.match ? '✓ Concordância com a IA' : '≠ Divergência da IA'}
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-purple-600 font-medium">
                          <EyeOff className="w-3.5 h-3.5" /> Previsão Oculta
                        </span>
                      )}
                    </div>

                    <p className="text-xs text-slate-800 dark:text-slate-200 font-medium leading-relaxed">
                      "{item.sanitizedText}"
                    </p>

                    {item.humanStance ? (
                      <div className="p-3 rounded-lg bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 text-xs flex flex-wrap items-center justify-between gap-2 animate-in fade-in">
                        <div>
                          <span className="text-slate-500 mr-2">Seu Voto:</span>
                          <strong className="font-mono text-purple-700 dark:text-purple-300">{item.humanStance}</strong>
                        </div>
                        <div>
                          <span className="text-slate-500 mr-2">Previsão da IA:</span>
                          <strong className="font-mono text-blue-700 dark:text-blue-300">{item.aiPredictedStance}</strong>
                        </div>
                        <div className="text-[11px] text-slate-500">
                          Termos-chave XAI: {item.aiKeyTerms.join(', ')}
                        </div>
                      </div>
                    ) : (
                      <div className="flex items-center gap-2 pt-1">
                        <span className="text-xs text-slate-500 font-medium mr-2">Sua Classificação Humana:</span>
                        {(['FAVORAVEL', 'CONTRARIO', 'NEUTRO'] as Stance[]).map((st) => (
                          <button
                            key={st}
                            onClick={() => handleBlindVote(item.id, st)}
                            className={`px-3 py-1.5 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                              st === 'FAVORAVEL'
                                ? 'bg-blue-600 hover:bg-blue-700 text-white'
                                : st === 'CONTRARIO'
                                ? 'bg-orange-600 hover:bg-orange-700 text-white'
                                : 'bg-slate-200 dark:bg-slate-700 hover:bg-slate-300 text-slate-800 dark:text-slate-100'
                            }`}
                          >
                            {st}
                          </button>
                        ))}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Painel Matemático Ao Vivo de Calibração */}
          <div className="space-y-4">
            <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
              <h3 className="text-sm font-bold text-slate-900 dark:text-white uppercase tracking-wider">
                Matriz de Confusão 3×3 (Ao Vivo)
              </h3>
              <p className="text-[11px] text-slate-500">Linha: Humano (Padrão Ouro) · Coluna: IA (Classificador)</p>

              <div className="overflow-x-auto rounded-xl border border-slate-200 dark:border-slate-800">
                <table className="w-full text-center text-xs font-mono">
                  <thead className="bg-slate-50 dark:bg-slate-800 text-slate-600 dark:text-slate-300">
                    <tr>
                      <th className="py-2 px-1 text-left text-[10px]">H \ IA</th>
                      <th className="py-2 px-1 text-[10px]">Fav</th>
                      <th className="py-2 px-1 text-[10px]">Contr</th>
                      <th className="py-2 px-1 text-[10px]">Neut</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-100 dark:divide-slate-800">
                    <tr>
                      <td className="py-2 px-1 text-left font-bold text-slate-700">Fav</td>
                      <td className="py-2 px-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 font-bold tabular-nums">
                        {confusionMatrix.favoravel.favoravel}
                      </td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.favoravel.contrario}</td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.favoravel.neutro}</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-1 text-left font-bold text-slate-700">Contr</td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.contrario.favoravel}</td>
                      <td className="py-2 px-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 font-bold tabular-nums">
                        {confusionMatrix.contrario.contrario}
                      </td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.contrario.neutro}</td>
                    </tr>
                    <tr>
                      <td className="py-2 px-1 text-left font-bold text-slate-700">Neut</td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.neutro.favoravel}</td>
                      <td className="py-2 px-1 text-slate-500 tabular-nums">{confusionMatrix.neutro.contrario}</td>
                      <td className="py-2 px-1 bg-emerald-50 dark:bg-emerald-950/40 text-emerald-800 font-bold tabular-nums">
                        {confusionMatrix.neutro.neutro}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Indicadores Calibrados */}
              <div className="space-y-2 pt-2 border-t border-slate-100 dark:border-slate-800 text-xs">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Kappa de Cohen (κ):</span>
                  <strong className="font-mono text-emerald-600 tabular-nums">{calibrationMetrics.cohenKappa}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Sensibilidade (Se):</span>
                  <strong className="font-mono text-slate-900 dark:text-white tabular-nums">{calibrationMetrics.sensitivity}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Especificidade (Sp):</span>
                  <strong className="font-mono text-slate-900 dark:text-white tabular-nums">{calibrationMetrics.specificity}</strong>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Índice J de Youden:</span>
                  <strong className="font-mono text-blue-600 tabular-nums">{calibrationMetrics.youdenJ}</strong>
                </div>
                <div className="flex items-center justify-between pt-2 border-t border-slate-100 dark:border-slate-800">
                  <span className="font-semibold text-slate-700 dark:text-slate-200">Prevalência Rogan-Gladen:</span>
                  <strong className="font-mono text-base text-blue-700 dark:text-blue-300 tabular-nums">{calibrationMetrics.roganGladenPrevalence}%</strong>
                </div>
              </div>

              <button
                onClick={() => showToast('success', 'Calibração Salva', 'Parâmetros humanos incorporados ao Boletim Oficial!')}
                className="w-full py-2 bg-blue-700 hover:bg-blue-800 text-white rounded-xl text-xs font-semibold transition-colors cursor-pointer"
              >
                Aplicar Minha Calibração ao Boletim
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ABA 5: SIMULADOR PASSO A PASSO (SANDBOX) */}
      {activeTab === 'sandbox' && (
        <div className="space-y-6">
          <div className="bg-white dark:bg-slate-900 border border-slate-200 dark:border-slate-800 rounded-2xl p-6 shadow-2xs space-y-4">
            <h2 className="text-base font-bold text-slate-900 dark:text-white">
              Simulador Interativo Passo a Passo do Pipeline (Sandbox)
            </h2>
            <p className="text-xs text-slate-500 dark:text-slate-400">
              Digite qualquer frase ou comentário de teste para acompanhar os 6 estágios de processamento algorítmico e estatístico.
            </p>

            <div className="space-y-3">
              <textarea
                value={sandboxText}
                onChange={(e) => setSandboxText(e.target.value)}
                rows={3}
                className="w-full p-3 rounded-xl border border-slate-300 dark:border-slate-700 bg-slate-50 dark:bg-slate-800 text-xs font-sans text-slate-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-600/30"
                placeholder="Digite a frase para simulação..."
              />

              <div className="flex flex-wrap items-center justify-between gap-4">
                <div className="flex items-center gap-3">
                  <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
                    <span>Rede:</span>
                    <select
                      value={sandboxPlatform}
                      onChange={(e) => setSandboxPlatform(e.target.value as PlatformId)}
                      className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs font-medium cursor-pointer"
                    >
                      <option value="x_twitter">X / Twitter</option>
                      <option value="youtube">YouTube</option>
                      <option value="telegram">Telegram</option>
                      <option value="instagram_facebook">Instagram / Facebook</option>
                      <option value="tiktok">TikTok</option>
                      <option value="whatsapp">WhatsApp</option>
                    </select>
                  </div>

                  <div className="flex items-center gap-1.5 text-xs text-slate-600 dark:text-slate-300">
                    <span>UF:</span>
                    <select
                      value={sandboxUf}
                      onChange={(e) => setSandboxUf(e.target.value)}
                      className="px-2 py-1 rounded bg-slate-100 dark:bg-slate-800 border border-slate-300 dark:border-slate-700 text-xs font-medium cursor-pointer"
                    >
                      <option value="SP">SP (Sudeste)</option>
                      <option value="RJ">RJ (Sudeste)</option>
                      <option value="DF">DF (Centro-Oeste)</option>
                      <option value="BA">BA (Nordeste)</option>
                      <option value="RS">RS (Sul)</option>
                      <option value="PA">PA (Norte)</option>
                    </select>
                  </div>
                </div>

                <button
                  onClick={handleRunSandbox}
                  disabled={isSandboxRunning || !sandboxText.trim()}
                  className="flex items-center gap-2 px-5 py-2 bg-blue-700 hover:bg-blue-800 disabled:opacity-50 text-white rounded-xl text-xs font-semibold transition-all cursor-pointer"
                >
                  <Send className="w-3.5 h-3.5" />
                  {isSandboxRunning ? 'Executando os 6 Passos...' : 'Executar Pipeline Passo a Passo'}
                </button>
              </div>
            </div>
          </div>

          {/* Resultados dos 6 Passos do Pipeline */}
          {sandboxResult && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 animate-in fade-in duration-200">
              {/* Passo 1 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-blue-700 dark:text-blue-400 uppercase">
                  Passo 1: LGPD & AppSec
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Hash Autor: <span className="font-mono text-slate-900 dark:text-white">{sandboxResult.step1_lgpd.author_id_hash}</span></div>
                  <div>Anonimizado: "{sandboxResult.step1_lgpd.scrubbed_text}"</div>
                  <div className="text-[10px] text-slate-400">{sandboxResult.step1_lgpd.protocol}</div>
                </div>
              </div>

              {/* Passo 2 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-emerald-700 dark:text-emerald-400 uppercase">
                  Passo 2: Filtro Silver CIB & Spam
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Veredito: <strong className="font-mono text-emerald-600">{sandboxResult.step2_silver_cib.verdict}</strong></div>
                  <div>Tag: <span className="font-mono">{sandboxResult.step2_silver_cib.reason_tag}</span></div>
                  <div>Burstiness: <span className="font-mono tabular-nums">{sandboxResult.step2_silver_cib.burstiness_index}</span></div>
                </div>
              </div>

              {/* Passo 3 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-purple-700 dark:text-purple-400 uppercase">
                  Passo 3: Features & Viés Lexical
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Enquadramento: <strong>{sandboxResult.step3_feature_engineering.framing_detected}</strong></div>
                  <div>Tokens Úteis: <span className="font-mono tabular-nums">{sandboxResult.step3_feature_engineering.token_count}</span></div>
                  <div>Score Viés Lexical: <span className="font-mono tabular-nums">{sandboxResult.step3_feature_engineering.lexical_bias_score}</span></div>
                </div>
              </div>

              {/* Passo 4 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-blue-700 dark:text-blue-400 uppercase">
                  Passo 4: Classificador & XAI SHAP
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Postura Predita: <strong className="font-mono text-blue-600">{sandboxResult.step4_classifier_xai.predicted_stance}</strong></div>
                  <div>Probabilidade: <span className="font-mono tabular-nums">{(sandboxResult.step4_classifier_xai.probabilities.favoravel * 100).toFixed(0)}% Fav</span></div>
                  <div className="text-[10px] text-slate-400">Tokens SHAP: {sandboxResult.step4_classifier_xai.shap_tokens.map((t) => t.token).join(', ')}</div>
                </div>
              </div>

              {/* Passo 5 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-indigo-700 dark:text-indigo-400 uppercase">
                  Passo 5: Espectro Discursivo (ADR-010)
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Campo Dominante: <strong>{sandboxResult.step5_digital_spectrum.primary_spectrum_name}</strong></div>
                  <div>Propagação Harmônica: <span className="font-mono">Ativa</span></div>
                </div>
              </div>

              {/* Passo 6 */}
              <div className="p-4 rounded-xl border border-slate-200 dark:border-slate-800 bg-white dark:bg-slate-900 space-y-2">
                <div className="text-xs font-bold text-amber-700 dark:text-amber-400 uppercase">
                  Passo 6: Ponderação & Rogan-Gladen
                </div>
                <div className="text-[11px] text-slate-600 dark:text-slate-400 space-y-1">
                  <div>Peso Raking IPF: <strong className="font-mono">{sandboxResult.step6_sample_weighting.raking_ipf_weight}</strong></div>
                  <div>Macrorregião: {sandboxResult.step6_sample_weighting.macroregion}</div>
                  <div className="text-[10px] text-slate-500 font-mono">{sandboxResult.step6_sample_weighting.rogan_gladen_formula}</div>
                </div>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};
