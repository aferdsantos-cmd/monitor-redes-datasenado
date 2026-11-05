# Tokens Institucionais DataSenado, Tipografia Tabular e Protocolo Anti-AI-Slop

Este manual técnico formaliza a arquitetura de tokens visuais, paletas semânticas cromáticas e a lista de restrições estéticas para erradicação de padrões genéricos gerados por inteligência artificial (*AI-Slop*) na interface do Monitor de Redes DataSenado.

---

## 1. Arquitetura de Tokens de Cor e Superfície

A interface da bancada analítica do DataSenado é projetada para servidores públicos, consultores legislativos e pesquisadores que passam longas horas analisando dados. O design deve transmitir sobriedade institucional, precisão pericial e estabilidade.

### 1.1 Superfícies, Textos e Bordas Capilares
| Elemento Token | Modo Claro Editorial | Modo Escuro Bancada | Regra CSS / Tailwind |
| :--- | :--- | :--- | :--- |
| **Fundo de Aplicação (Canvas)** | `#F8FAFC` (`slate-50`) | `#090D16` | Contraste de fundo relaxado, sem reflexos |
| **Superfície de Painel (Cards)** | `#FFFFFF` (`white`) | `#0F172A` (`slate-900`) | Separação física clara de zonas de dados |
| **Bordas Estruturais** | `#E2E8F0` (`slate-200`) | `#1E293B` (`slate-800`) | Bordas capilares exatas de `1px` (`border`) |
| **Texto Primário (Corpo/KPIs)** | `#0F172A` (`slate-900`) | `#F8FAFC` (`slate-50`) | Contraste WCAG AAA $\ge 7.0:1$ |
| **Texto Secundário (Metadados)**| `#475569` (`slate-600`) | `#94A3B8` (`slate-400`) | Contraste WCAG AA $\ge 4.5:1$ |
| **Acento Institucional Senado** | `#0B1F3A` / `#1E3A8A` | `#3B82F6` / `#60A5FA` | Identidade visual oficial do Senado Federal |
| **Acento Dourado Sóbrio** | `#B45309` (`amber-700`) | `#F59E0B` (`amber-500`) | Realce moderado de alertas institucionais |

---

## 2. Paleta Semântica Científica Okabe-Ito (100% Segura para Daltônicos)

Em gráficos estatísticos e categorizações temáticas, o uso de paletas arbitrárias verde/vermelho introduz barreiras severas para pessoas com daltonismo (especialmente deuteranopia e protanopia). Adota-se a paleta científica universal de Okabe & Ito (2002):

```json
{
  "stance_colors": {
    "FAVORAVEL": "#0072B2",
    "CONTRARIO": "#D55E00",
    "NEUTRO_INFORMATIVO": "#64748B"
  },
  "bubble_spectrum_colors": {
    "PROGRESSISTA": "#009E73",
    "CONSERVADOR": "#D55E00",
    "CENTRO_INSTITUCIONAL": "#0072B2",
    "TECNICO_SETORIAL": "#CC79A7"
  },
  "audit_quarantine_colors": {
    "ORGANICO_VERIFICADO": "#009E73",
    "SPAM_COMERCIAL": "#D97706",
    "CIB_COORDENADO": "#DC2626"
  }
}
```

---

## 3. Tipografia de Precisão e Regra Compulsória `tabular-nums`

Dígitos numéricos com largura proporcional (padrão em fontes modernas) variam de largura conforme o algarismo (o número "1" é muito mais estreito que o "8"). Quando valores mudam em tempo real ou quando tabelas são inspecionadas verticalmente, os decimais e alinhamentos oscilam, provocando fadiga visual e leitura truncada.

### 3.1 Padrão Obrigatório
- Em todos os elementos que contenham dados quantitativos (contagens de amostra $n$, universo $N_{\text{org}}$, intervalos `[42,1% — 47,9%]`, hashes encurtados, datas e tempos), a classe Tailwind `tabular-nums` (`font-variant-numeric: tabular-nums`) deve ser aplicada:
```tsx
// Correto: alinhamento perfeito de colunas decimais
<span className="font-mono text-sm tabular-nums text-slate-900 dark:text-slate-50">
  45.8% (IC 95%: [43.1% — 48.5%])
</span>
```

---

## 4. Lista Negra de Clichês de "IA Genérica" (*AI-Slop Blacklist*)

Ferramentas automáticas e protótipos de baixa qualidade frequentemente recorrem a uma linguagem visual artificial, vulgarmente chamada de *AI-Slop*. Na interface da Bancada do DataSenado, esses elementos são terminantemente proibidos:

1. **Gradientes Neon Estridentes:**
   - Proibido: `bg-gradient-to-r from-indigo-500 via-purple-500 to-pink-500` ou combinações de azul ciano com magenta neon.
   - Padrão: Fundos monocromáticos neutros com acentos sóbrios e estruturados.
2. **Sombras Coloridas e Glow Effects:**
   - Proibido: `shadow-indigo-500/50`, `drop-shadow-[0_0_15px_rgba(99,102,241,0.5)]`.
   - Padrão: Sombras estruturais sutis (`shadow-sm` cinza neutro) e bordas capilares de `1px` (`border-slate-200 dark:border-slate-800`).
3. **Cantos Excessivamente Arredondados:**
   - Proibido: `rounded-3xl` ou `rounded-full` em cards analíticos, tabelas e gráficos.
   - Padrão: Raios moderados e profissionais (`rounded-md` / `rounded-lg` de 6px a 8px).
4. **Emojis em Títulos e Botões Operacionais:**
   - Proibido: `"🚀 Iniciar Monitoramento"`, `"📊 Gráficos de Redes"`, `"🔥 Tendências"`.
   - Padrão: Texto técnico conciso acompanhado de ícones vetoriais monocromáticos **Lucide React** (`w-4 h-4`, `strokeWidth={1.75}`, `aria-hidden="true"`).
