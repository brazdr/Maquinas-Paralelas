"""
Iterated Local Search (ILS) para o Problema de Máquinas Paralelas Idênticas
com Restrições de Precedência
--------------------------------------------------------------------------------
Instância: 40 tarefas, 5 máquinas idênticas, com relações de prioridade
(algumas tarefas precisam terminar antes que outras possam começar) e
não preempção (uma tarefa, uma vez iniciada, deve ser concluída sem
interrupção, mesmo que isso obrigue outra tarefa a esperar).

Como o makespan é calculado aqui:
Diferente das instâncias fácil/média (onde a carga de uma máquina é
simplesmente a SOMA dos tempos das tarefas nela alocadas), aqui não basta
somar: uma tarefa só pode começar quando (i) a máquina estiver livre e
(ii) todas as suas tarefas predecessoras já tiverem terminado (em
qualquer máquina). Por isso o makespan é obtido por SIMULAÇÃO:
  1. Calcula-se uma ordem topológica das tarefas (respeitando as
     precedências, com desempate por LPT - tarefas mais longas primeiro
     entre as que já estão liberadas).
  2. Processa-se essa ordem, e para cada tarefa:
       início = max(instante em que a máquina alocada fica livre,
                    maior instante de término entre as predecessoras)
       término = início + tempo de processamento
  3. O makespan é o maior instante de término entre as 5 máquinas.

Lê os dados do arquivo "dados_maquinas_paralelas_dificil.txt" 
"""

import re
import time
import random
import heapq
from pathlib import Path

def ler_instancia(caminho):
    texto = Path(caminho).read_text(encoding="utf-8")

    n_maquinas = int(re.search(r"Número de máquinas:\s*(\d+)", texto).group(1))

    tarefas = {}
    precedencia = {}  
    for linha in texto.splitlines():
        m = re.match(
            r"\s*(\d+)\s+(\d+)\s+(Nenhuma|Prioridade:\s*\[([\d,\s]+)\])", linha
        )
        if m:
            tid, tempo = int(m.group(1)), int(m.group(2))
            tarefas[tid] = tempo
            if m.group(4):
                sucessoras = [int(x) for x in m.group(4).split(",")]
                precedencia[tid] = sucessoras

    return tarefas, n_maquinas, precedencia

def ordem_topologica(tarefas, precedencia):
    sucessoras_de = {t: [] for t in tarefas}
    grau_entrada = {t: 0 for t in tarefas}
    for t, sucessoras in precedencia.items():
        for s in sucessoras:
            sucessoras_de[t].append(s)
            grau_entrada[s] += 1

    fila = [(-tarefas[t], t) for t in tarefas if grau_entrada[t] == 0]
    heapq.heapify(fila)
    ordem = []
    while fila:
        _, t = heapq.heappop(fila)
        ordem.append(t)
        for s in sucessoras_de[t]:
            grau_entrada[s] -= 1
            if grau_entrada[s] == 0:
                heapq.heappush(fila, (-tarefas[s], s))
    return ordem


def predecessoras_de(precedencia):
    """Inverte o dicionário: para cada tarefa, quais são suas predecessoras."""
    preds = {}
    for t, sucessoras in precedencia.items():
        for s in sucessoras:
            preds.setdefault(s, []).append(t)
    return preds

def makespan(atribuicao, ordem, tarefas, n_maquinas, preds):
    maquina_livre = [0] * n_maquinas
    termino = {}
    for t in ordem:
        m = atribuicao[t]
        pronto_em = 0
        for p in preds.get(t, []):
            pronto_em = max(pronto_em, termino[p])
        inicio = max(maquina_livre[m], pronto_em)
        fim = inicio + tarefas[t]
        termino[t] = fim
        maquina_livre[m] = fim
    return max(maquina_livre), maquina_livre, termino

def construcao_gulosa(tarefas, ordem, n_maquinas, preds):
    maquina_livre = [0] * n_maquinas
    termino = {}
    atribuicao = {}
    for t in ordem:
        pronto_em = 0
        for p in preds.get(t, []):
            pronto_em = max(pronto_em, termino[p])
        melhor_m, melhor_fim = None, None
        for m in range(n_maquinas):
            inicio = max(maquina_livre[m], pronto_em)
            fim = inicio + tarefas[t]
            if melhor_fim is None or fim < melhor_fim:
                melhor_fim, melhor_m = fim, m
        atribuicao[t] = melhor_m
        termino[t] = melhor_fim
        maquina_livre[melhor_m] = melhor_fim
    return atribuicao

def busca_local(atribuicao, ordem, tarefas, n_maquinas, preds, max_varreduras=100):
    atual = dict(atribuicao)
    custo_atual, _, _ = makespan(atual, ordem, tarefas, n_maquinas, preds)

    for _ in range(max_varreduras):
        melhor_move, melhor_custo = None, custo_atual
        for t in tarefas:
            m_original = atual[t]
            for m in range(n_maquinas):
                if m == m_original:
                    continue
                teste = atual.copy()
                teste[t] = m
                custo, _, _ = makespan(teste, ordem, tarefas, n_maquinas, preds)
                if custo < melhor_custo:
                    melhor_custo, melhor_move = custo, teste
        if melhor_move is None:
            break
        atual, custo_atual = melhor_move, melhor_custo

    return atual, custo_atual

def perturbacao(atribuicao, nivel, n_maquinas, rng):
    novo = dict(atribuicao)
    tarefas_ids = list(atribuicao.keys())
    k = min(nivel, len(tarefas_ids))
    escolhidas = rng.sample(tarefas_ids, k)
    for t in escolhidas:
        outras_maquinas = [m for m in range(n_maquinas) if m != novo[t]]
        novo[t] = rng.choice(outras_maquinas)
    return novo

def ils(tarefas, n_maquinas, precedencia, ils_max=50, tempo_limite=60, seed=42):
    rng = random.Random(seed)
    t0 = time.time()

    ordem = ordem_topologica(tarefas, precedencia)
    preds = predecessoras_de(precedencia)

    s0 = construcao_gulosa(tarefas, ordem, n_maquinas, preds)
    s, custo = busca_local(s0, ordem, tarefas, n_maquinas, preds)

    historico = [custo]
    iteracao, melhor_iteracao, nivel = 0, 0, 1
    nivel_max = max(2, len(tarefas) // 4)

    while iteracao - melhor_iteracao < ils_max:
        iteracao += 1

        s_linha = perturbacao(s, nivel + 1, n_maquinas, rng)
        s_2linhas, custo_2linhas = busca_local(s_linha, ordem, tarefas, n_maquinas, preds)

        if custo_2linhas < custo:
            s, custo = s_2linhas, custo_2linhas
            melhor_iteracao = iteracao
            nivel = 1                      
        else:
            nivel = min(nivel + 1, nivel_max)   

        historico.append(custo)

        if time.time() - t0 > tempo_limite:
            break

    tempo_execucao = time.time() - t0
    _, _, termino = makespan(s, ordem, tarefas, n_maquinas, preds)

    return {
        "atribuicao": s,
        "makespan": custo,
        "historico": historico,
        "tempo_execucao": tempo_execucao,
        "iteracoes": iteracao,
        "termino": termino,
        "ordem": ordem,
    }

def relatorio(tarefas, n_maquinas, precedencia, resultado):
    atribuicao = resultado["atribuicao"]

    maquinas = {m: [] for m in range(n_maquinas)}
    for t, m in atribuicao.items():
        maquinas[m].append(t)

    print("=" * 70)
    print("RELATÓRIO - PROBLEMA DE MÁQUINAS PARALELAS (INSTÂNCIA DIFÍCIL)")
    print("=" * 70)
    print(f"Nº de tarefas: {len(tarefas)} | Nº de máquinas: {n_maquinas}")
    print(f"Nº de restrições de precedência: {len(precedencia)}\n")

    print("a) Atribuição final de tarefas às máquinas "
          "(ordem = sequência de execução na máquina):")
    for m in range(n_maquinas):
        tarefas_m = sorted(maquinas[m], key=lambda t: resultado["termino"][t])
        carga = sum(tarefas[t] for t in maquinas[m])
        print(f"   Máquina {m + 1}: {tarefas_m} "
              f"-> soma dos tempos = {carga}, término em {max((resultado['termino'][t] for t in maquinas[m]), default=0)}")

    print(f"\nb) Valor final do makespan (Cmax): {resultado['makespan']}")

    print(f"\nc) Tempo de execução do algoritmo: "
          f"{resultado['tempo_execucao']:.4f} segundos "
          f"({resultado['iteracoes']} iterações do ILS)")

    hist = resultado["historico"]
    print(f"\nd) Evolução do makespan ao longo das iterações do ILS:")
    print(f"   Início (após 1ª busca local): {hist[0]}")
    print(f"   Fim (melhor solução encontrada): {hist[-1]}")
    print(f"   Histórico completo: {hist}")

if __name__ == "__main__":
    caminho_dados = Path(__file__).parent / "dados_maquinas_paralelas_dificil.txt"

    tarefas, n_maquinas, precedencia = ler_instancia(caminho_dados)
    resultado = ils(tarefas, n_maquinas, precedencia, ils_max=50, tempo_limite=60, seed=42)
    relatorio(tarefas, n_maquinas, precedencia, resultado)