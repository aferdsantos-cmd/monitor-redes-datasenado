# Fronteiras Epistemológicas, Vocabulário Controlado e Referências Canônicas

Este documento estabelece o padrão de rigor metodológico, delimitação inferencial, matriz de ameaças à validade científica e referências bibliográficas canônicas para o TCC em Ciência de Dados e para a assessoria técnica parlamentar do Instituto de Pesquisa DataSenado.

---

## 1. Glossário de Precisão Conceitual: Termos Proibidos vs. Termos Corretos

Para mitigar o viés clássico de supergeneralização de rastros digitais (*Big Data Paradox*, Meng, 2018; Bethlehem, 2010), adota-se o seguinte vocabulário controlado:

| ❌ Termo Impreciso / Proibido | ✅ Termo Metodologicamente Correto | Justificativa Científica |
| :--- | :--- | :--- |
| "A opinião dos brasileiros sobre o projeto..." | "O clima de posicionamento no Universo Observado de Contas Digitais Orgânicas ($\mathcal{U}_{\text{Org}, T}$)..." | Redes sociais sofrem de autosseleção severa e não representam a totalidade da população do país. |
| "1 Cidadão = 1 Opinião" | "1 Conta Digital Orgânica por Plataforma = 1 Unidade Observacional" | Sob a LGPD e limites de API, é impossível associar deterministicamente contas de plataformas distintas a um mesmo CPF. |
| "Margem de erro da pesquisa: ±3%" | "Incerteza estatística interna do sorteio amostral / reamostragem bootstrap: ±3 p.p." | Não há margem de erro populacional em dados observacionais de conveniência/rastros digitais. |
| "Amostra probabilística da população" | "Amostra estratificada interna de contas orgânicas sorteadas a partir do universo observado" | A probabilidade de inclusão na coleta original é desconhecida; o sorteio é probabilístico apenas *dentro* do universo coletado. |
| "Correção demográfica perfeita (MRP)" | "Cenário 3 Reponderado: Análise de Sensibilidade via Raking IPF sob Hipótese de Ignorabilidade" | Redes não fornecem covariáveis demográficas completas e confiáveis para MRP individual. |
| "Robôs foram 100% eliminados" | "Remoção de contas com indícios estatísticos de comportamento inautêntico coordenado (CIB) e automação" | Detecção de CIB opera por heurísticas e limiares estatísticos, sujeita a taxas controladas de sensibilidade e especificidade. |
| "Anonimização de usuários" | "Pseudonimização via HMAC-SHA256 (dado pessoal mantido sob regime de segurança, LGPD art. 13, §4º)" | Chaves criptográficas mantêm a reidentificabilidade sob custódia, não constituindo anonimização irreversível plena. |

---

## 2. Matriz de Ameaças à Validade Científica (Shadish, Cook & Campbell, 2002)

O desenho metodológico implementado responde explicitamente aos quatro tipos fundamentais de validade científica:

| Dimensão de Validade | Ameaça Identificada no Debate Digital | Salvaguarda e Mecanismo de Controle Implementado |
| :--- | :--- | :--- |
| **Validade de Conclusão Estatística (SCE)** | Variância inflacionada por pesos dispersos, violação de i.i.d., erro tipo I em múltiplos testes. | - Cálculo de $\text{DEFF}_{\text{Kish}}$ e tamanho efetivo $n_{\text{eff}}$.<br>- Alocação exata de Hamilton ($\sum n_h = n$).<br>- Intervalos de confiança de 95% via Bootstrap Estratificado.<br>- Ajuste de Holm-Bonferroni para comparações múltiplas. |
| **Validade Interna (VI)** | Falsos positivos por contaminação de bots/CIB e distorção em notícias virais orgânicas. | - Detecção em duas etapas: LSH + Jaccard $\ge 0.85$ e Grafo de Leiden com repetição de co-ocorrência.<br>- *Allowlist* jornalística/governamental.<br>- Exclusão em nível de conta (`account_suspected_cib`). |
| **Validade de Construto (VC)** | Erro de classificação do classificador de linguagem natural (NLP) gerando viés na proporção. | - Correção analítica clássica de **Rogan & Gladen (1978)** ajustada pelas taxas de Sensibilidade ($\text{TPR}$) e Especificidade ($\text{TNR}$). |
| **Validade Externa (VE)** | Supergeneralização indevida dos dados das redes para o conjunto do eleitorado brasileiro. | - Delimitação epistemológica restrita a $\mathcal{U}_{\text{Org}, T}$.<br>- Apresentação dos 3 cenários (C1, C2, C3) lado a lado.<br>- Cenário 3 explicitamente documentado como análise de sensibilidade. |

---

## 3. Mapeamento de Lacunas na Literatura (Research Gaps do TCC)

A pesquisa preenche duas lacunas estruturais nos estudos de comunicação digital e escuta social legislativa:

1. **Lacuna 1 (Vulnerabilidade do Social Listening Tradicional ao Big Data Paradox):** Os monitoramentos parlamentares convencionais utilizam métricas baseadas exclusivamente em contagem bruta de menções (*volume-based social listening*). Conforme demonstrado por Meng (2018), em grandes bases observacionais desprovidas de controle probabilístico, pequenos vieses de autosseleção e amplificação mecânica de redes coordenadas (CIB) dominam a variância e produzem falsas maiorias parlamentares com alta certeza aparente.
2. **Lacuna 2 (Inexistência de Pipeline Aberto Integrado sob Política Zero-Footprint):** Falta na literatura nacional ferramenta computacional transparente e reprodutível que una: (a) desinfecção de redes coordenadas via algoritmos comunitários de grafos (*Leiden*), (b) amostragem estratificada probabilística com alocação ótima, (c) calibração por Raking IPF com limites estritos no simplex e (d) correção de Rogan-Gladen, tudo operando sob política de cache efêmero (*Zero-Footprint*) em máquinas locais modestas.

---

## 4. Referências Bibliográficas Canônicas (ABNT NBR 6023 / NBR 10520:2023) com DOI

1. **BAKER, R. et al.** Summary Report of the AAPOR Task Force on Non-probability Sampling. *Journal of Survey Statistics and Methodology*, v. 1, n. 2, p. 90–143, 2013. DOI: `https://doi.org/10.1093/jssam/smt008`.
2. **BETHLEHEM, J.** Selection Bias in Web Surveys. *International Statistical Review*, v. 78, n. 2, p. 161–188, 2010. DOI: `https://doi.org/10.1111/j.1751-5823.2010.00112.x`.
3. **COCHRAN, W. G.** *Sampling Techniques*. 3. ed. New York: John Wiley & Sons, 1977. ISBN: 978-0-471-16240-7.
4. **DEMING, W. E.; STEPHAN, F. F.** On a Least Squares Adjustment of a Sampled Frequency Table When the Expected Marginal Totals are Known. *The Annals of Mathematical Statistics*, v. 11, n. 4, p. 427–444, 1940. DOI: `https://doi.org/10.1214/aoms/1177731829`.
5. **ELLIOTT, M. R.; VALLIANT, R.** Inference for Nonprobability Samples. *Statistical Science*, v. 32, n. 2, p. 249–264, 2017. DOI: `https://doi.org/10.1214/16-STS598`.
6. **GIGLIETTO, F. et al.** It takes a village to manipulate the media: coordinated link sharing behavior. *Information, Communication & Society*, v. 23, n. 6, p. 867–891, 2020. DOI: `https://doi.org/10.1080/1369118X.2020.1754877`.
7. **KISH, L.** *Survey Sampling*. New York: John Wiley & Sons, 1965. ISBN: 978-0-471-10949-5.
8. **KISH, L.** Weighting for Unequal $P_i$. *Journal of Official Statistics*, v. 8, n. 2, p. 183–200, 1992. URI: `https://www.scb.se/jos`.
9. **MENG, X.-L.** Statistical Paradises and Paradoxes in Big Data (I): Law of Large Populations, Big Data Paradox, and the 2016 US Presidential Election. *The Annals of Applied Statistics*, v. 12, n. 2, p. 685–726, 2018. DOI: `https://doi.org/10.1214/18-AOAS1161SF`.
10. **PACHECO, D. et al.** Uncovering Coordinated Networks on Social Media: Methods and Case Studies. In: *International AAAI Conference on Web and Social Media (ICWSM)*, 15., 2021. Proceedings... p. 455–466. DOI: `https://doi.org/10.1609/icwsm.v15i1.18075`.
11. **RAUCHFLEISCH, A.; KAISER, J.** The False Positive Problem of Automatic Bot Detection in Social Science Research. *PLOS ONE*, v. 15, n. 10, e0241045, 2020. DOI: `https://doi.org/10.1371/journal.pone.0241045`.
12. **ROGAN, W. J.; GLADEN, B.** Estimating Prevalence from the Results of a Screening Test. *American Journal of Epidemiology*, v. 107, n. 1, p. 71–76, 1978. DOI: `https://doi.org/10.1093/oxfordjournals.aje.a112510`.
13. **TRAAG, V. A.; WALTMAN, L.; VAN ECK, N. J.** From Louvain to Leiden: guaranteeing well-connected communities. *Scientific Reports*, v. 9, n. 1, 5233, 2019. DOI: `https://doi.org/10.1038/s41598-019-41695-z`.
14. **VALLIANT, R.; DEVER, J. A.; KREUTER, F.** *Practical Tools for Designing and Weighting Survey Samples*. 2. ed. Cham: Springer, 2018. DOI: `https://doi.org/10.1007/978-3-319-93632-1`.
