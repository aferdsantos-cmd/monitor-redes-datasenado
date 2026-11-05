# Estado de URL com Nuqs, Validação Zod e TanStack Query sob Zero-Footprint

Este manual técnico estabelece a arquitetura de sincronização reativa de filtros na URL, contratos de validação estritos espelhados entre TypeScript (Zod) e Python (Pydantic), e padrões de carregamento assíncrono com eliminação absoluta de deslocamentos de layout (*Cumulative Layout Shift - CLS = 0*).

---

## 1. Sincronização de Filtros na URL via Nuqs (`useQueryState`)

Em aplicações analíticas, o estado dos filtros (janela de tempo, tema selecionado, plataformas ativas, cenário estatístico) deve residir na URL da página através de parâmetros de consulta (*query string*). Isso assegura:
1. **Compartilhamento de Visões:** O consultor legislativo pode copiar a URL do navegador e enviá-la a outro analista, que abrirá exatamente o mesmo recorte temporal e amostral;
2. **Histórico do Navegador:** Os botões "Voltar" e "Avançar" do navegador restauram os filtros anteriores sem recarregar a página;
3. **Persistência Sem LocalStorage:** Evita salvar estados em armazenamento local persistente no cliente.

### 1.1 Exemplo de Implementação com Nuqs
```tsx
import { useQueryState, parseAsString, parseAsInteger } from "nuqs";

export function useOperationalFilters() {
  const [themeId, setThemeId] = useQueryState("theme", parseAsString.withDefault("reforma_tributaria"));
  const [windowDays, setWindowDays] = useQueryState("days", parseAsInteger.withDefault(7));
  const [scenario, setScenario] = useQueryState("scenario", parseAsString.withDefault("C3_RAKING"));

  return { themeId, setThemeId, windowDays, setWindowDays, scenario, setScenario };
}
```

---

## 2. Contratos de Validação Espelhados com Zod e Pydantic

Para assegurar que o front-end nunca envie parâmetros ilegais para o backend DuckDB/Python:

### 2.1 Esquema Zod (TypeScript)
```ts
import { z } from "zod";

export const MonitoringWindowSpecSchema = z.object({
  theme_id: z.enum(["reforma_tributaria", "regulamentacao_ia", "seguranca_publica"]),
  window_days: z.number().int().min(1).max(90),
  selected_platforms: z.array(z.enum(["youtube", "telegram", "x", "meta", "tiktok", "whatsapp"])).min(1),
  target_sample_size_n: z.number().int().min(10).max(1000).default(30),
  scenario: z.enum(["C1_HAJEK", "C2_INV_WEIGHT", "C3_RAKING"]).default("C3_RAKING"),
  lexical_search_query: z.string().max(100).refine(
    (val) => !/\b(corrupto|genocida|salvador|mito)\b/i.test(val),
    { message: "Violação M-04: Termos valorativos polarizados são proibidos na busca temática neutra!" }
  ).optional(),
});

export type MonitoringWindowSpec = z.infer<typeof MonitoringWindowSpecSchema>;
```

---

## 3. Gestão Assíncrona com TanStack Query e Skeletons Geométricos (`CLS = 0`)

O atraso na resposta de consultas analíticas pesadas no DuckDB não pode provocar saltos visuais na página quando os dados chegam.

### 3.1 Padrão Skeleton-First
- Todo componente de gráfico ou KPI deve ter um correspondente `Skeleton` com **exatamente a mesma altura geométrica e raio de borda**:
```tsx
export function MetricCardSkeleton() {
  return (
    <div className="h-28 rounded-lg border border-slate-200 bg-white p-4 shadow-sm dark:border-slate-800 dark:bg-slate-900 animate-pulse">
      <div className="h-4 w-24 rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-3 h-8 w-32 rounded bg-slate-200 dark:bg-slate-800" />
      <div className="mt-2 h-3 w-40 rounded bg-slate-200 dark:bg-slate-800" />
    </div>
  );
}
```
Durante a transição de dados via `useQuery`, o layout permanece perfeitamente ancorado na página, garantindo medição `CLS == 0.00` em auditorias de Core Web Vitals.

---

## 4. Salvaguardas Zero-Footprint no Cliente
- **Proibição de Persistência Sensível:** É proibido invocar `localStorage.setItem()` ou `indexedDB` para armazenar textos literais de postagens, identificadores de autor ou credenciais.
- **Memória Efêmera:** As respostas analíticas do backend residem unicamente na memória volátil da aba ativa gerenciada pelo cache do `QueryClient`.
