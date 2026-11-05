# Primitivos Acessíveis (Radix UI / React Aria), Tailwind e Microinterações com Framer Motion

Este manual técnico detalha a implementação de componentes de interface ricos e acessíveis para o Monitor de Redes DataSenado, integrando primitivos WAI-ARIA, estilização utilitária e animações com respeito estrito à ergonomia cognitiva e acessibilidade motora.

---

## 1. Primitivos Acessíveis Radix UI e React Aria

Interfaces analíticas densas não podem comprometer a acessibilidade universal. O uso de elementos HTML puros desprovidos de semântica (como `<div onClick={...}>`) quebra a navegação por teclado e a compatibilidade com leitores de tela (NVDA, JAWS, VoiceOver).

### 1.1 Vantagens dos Primitivos Headless
1. **Gestão Automática de Foco (*Focus Trapping*):** Ao abrir um modal de detalhes (`Dialog`) ou gaveta lateral (`Sheet`), o foco do teclado é confinado ao modal e restaurado ao botão de origem após o fechamento (`Escape`).
2. **Atributos WAI-ARIA Completos:** Injeção dinâmica de `aria-expanded`, `aria-controls`, `aria-selected` e `aria-haspopup`.
3. **Navegação por Teclas Direcionais:** Em menus e abas (`Tabs`), o usuário navega entre opções com `ArrowDown`, `ArrowUp`, `Home` e `End`.

### 1.2 Padrão de Implementação de Toolbar
```tsx
import * as Toolbar from "@radix-ui/react-toolbar";
import { Calendar, Filter, Share2 } from "lucide-react";

export function OperationalToolbar() {
  return (
    <Toolbar.Root className="flex h-12 items-center gap-2 border-b border-slate-200 bg-white px-4 dark:border-slate-800 dark:bg-slate-900" aria-label="Controles Operacionais">
      <Toolbar.ToggleGroup type="single" defaultValue="7d" aria-label="Janela Temporal">
        <Toolbar.ToggleItem value="24h" className="rounded px-2.5 py-1 text-xs font-medium tabular-nums text-slate-700 hover:bg-slate-100 data-[state=on]:bg-blue-900 data-[state=on]:text-white dark:text-slate-300 dark:hover:bg-slate-800">
          24h
        </Toolbar.ToggleItem>
        <Toolbar.ToggleItem value="7d" className="rounded px-2.5 py-1 text-xs font-medium tabular-nums text-slate-700 hover:bg-slate-100 data-[state=on]:bg-blue-900 data-[state=on]:text-white dark:text-slate-300 dark:hover:bg-slate-800">
          7d
        </Toolbar.ToggleItem>
      </Toolbar.ToggleGroup>
      <Toolbar.Separator className="mx-2 h-5 w-[1px] bg-slate-200 dark:bg-slate-800" />
      <Toolbar.Button className="flex items-center gap-1.5 rounded bg-blue-800 px-3 py-1.5 text-xs font-semibold text-white hover:bg-blue-900 focus-visible:ring-2 focus-visible:ring-blue-600">
        <Filter className="h-3.5 w-3.5" aria-hidden="true" />
        Aplicar Filtros
      </Toolbar.Button>
    </Toolbar.Root>
  );
}
```

---

## 2. Dinamismo Orgânico e Microinterações com Framer Motion

Animações em interfaces institucionais e analíticas devem ter finalidade exclusivamente funcional: guiar a atenção do usuário para alterações de estado e transições de layout, sem introduzir lentidão percebida.

### 2.1 Calibração de Física de Mola (*Spring Physics*)
Em vez de curvas cúbicas duras (`ease-in-out`), adotam-se molas amortecidas que transmitem robustez e peso:
```ts
export const SENADO_SPRING_TRANSITION = {
  type: "spring",
  stiffness: 320,
  damping: 28,
  mass: 1.0,
};
```

### 2.2 Respeito Obrigatório a `prefers-reduced-motion`
Usuários com distúrbios vestibulares podem sofrer náuseas e tonturas com animações de deslizamento ou escala. O componente deve utilizar o hook `useReducedMotion()` do Framer Motion:
```tsx
import { motion, useReducedMotion } from "framer-motion";

export function AnimatedCard({ children }: { children: React.ReactNode }) {
  const shouldReduceMotion = useReducedMotion();
  const variants = {
    hidden: { opacity: 0, y: shouldReduceMotion ? 0 : 8 },
    visible: { opacity: 1, y: 0 },
  };

  return (
    <motion.div initial="hidden" animate="visible" variants={variants} transition={SENADO_SPRING_TRANSITION} className="rounded-lg border border-slate-200 bg-white p-4 dark:border-slate-800 dark:bg-slate-900">
      {children}
    </motion.div>
  );
}
```

---

## 3. Notificações Não-Bloqueantes com Sonner

Substitui completamente métodos invasivos e bloqueantes (`window.alert`, `window.confirm`):
```tsx
import { toast } from "sonner";

export function notifySampleCalibrated(nAccounts: number, elapsedSec: number) {
  toast.success("Amostra Gold Calibrada", {
    description: `Amostra de ${nAccounts} contas orgânicas calibrada via Raking IPF em ${elapsedSec}s.`,
    duration: 4000,
  });
}
```
As notificações do Sonner são empilhadas no canto inferior direito da tela, possuem contraste WCAG 2.2 e não interrompem a leitura de dados nem a digitação do operador.
