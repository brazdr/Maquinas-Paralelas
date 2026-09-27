"""
Iterated Local Search (ILS) para o Problema de Máquinas Paralelas Idênticas
----------------------------------------------------------------------------
Instância: 30 tarefas, 5 máquinas idênticas, tarefas independentes.
Objetivo: minimizar o makespan (Cmax) = tempo em que a última máquina termina.

Lê os dados do arquivo "dados_maquinas_paralelas_facil.txt"
"""

import re
import time
import random
from pathlib import Path

def ler_instancia(caminho):
    texto = Path(caminho).read_text(encoding="utf-8")

    n_maquinas = int(re.search(r"Número de máquinas:\s*(\d+)", texto).group(1))

    tarefas = {}
    for linha in texto.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s*$", linha)
        if m:
            tid, tempo = int(m.group(1)), int(m.group(2))
            tarefas[tid] = tempo

    return tarefas, n_maquinas

def makespan(atribuicao, tarefas, n_maquinas):
    carga = [0] * n_maquinas
    for t, m in atribuicao.items():
        carga[m] += tarefas[t]
    return max(carga), carga

def construcao_gulosa(tarefas, n_maquinas):
    ordem = sorted(tarefas, key=lambda t: -tarefas[t])  
    carga = [0] * n_maquinas
    atribuicao = {}
    for t in ordem:
        m = carga.index(min(carga))       
        atribuicao[t] = m
        carga[m] += tarefas[t]
    return atribuicao

def busca_local(atribuicao, tarefas, n_maquinas, max_varreduras=100):
    atual = dict(atribuicao)
    custo_atual, _ = makespan(atual, tarefas, n_maquinas)

    for _ in range(max_varreduras):
        melhor_move, melhor_custo = None, custo_atual
        for t in tarefas:
            m_original = atual[t]
            for m in range(n_maquinas):
                if m == m_original:
                    continue
                teste = atual.copy()
                teste[t] = m
                custo, _ = makespan(teste, tarefas, n_maquinas)
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

def ils(tarefas, n_maquinas, ils_max=50, tempo_limite=30, seed=42):
    rng = random.Random(seed)
    t0 = time.time()
    s0 = construcao_gulosa(tarefas, n_maquinas)
    s, custo = busca_local(s0, tarefas, n_maquinas)

    historico = [custo]
    iteracao, melhor_iteracao, nivel = 0, 0, 1
    nivel_max = max(2, len(tarefas) // 4)

    while iteracao - melhor_iteracao < ils_max:
        iteracao += 1

        s_linha = perturbacao(s, nivel + 1, n_maquinas, rng)
        s_2linhas, custo_2linhas = busca_local(s_linha, tarefas, n_maquinas)

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
    return {
        "atribuicao": s,
        "makespan": custo,
        "historico": historico,
        "tempo_execucao": tempo_execucao,
        "iteracoes": iteracao,
    }

def relatorio(tarefas, n_maquinas, resultado):
    atribuicao = resultado["atribuicao"]
    _, cargas = makespan(atribuicao, tarefas, n_maquinas)

    maquinas = {m: [] for m in range(n_maquinas)}
    for t, m in atribuicao.items():
        maquinas[m].append(t)

    print("=" * 60)
    print("RELATÓRIO - PROBLEMA DE MÁQUINAS PARALELAS (INSTÂNCIA FÁCIL)")
    print("=" * 60)
    print(f"Nº de tarefas: {len(tarefas)} | Nº de máquinas: {n_maquinas}\n")

    print("a) Atribuição final de tarefas às máquinas:")
    for m in range(n_maquinas):
        print(f"   Máquina {m + 1}: tarefas {sorted(maquinas[m])} "
              f"-> carga = {cargas[m]}")

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
    caminho_dados = Path(__file__).parent / "dados_maquinas_paralelas_facil.txt"

    tarefas, n_maquinas = ler_instancia(caminho_dados)
    resultado = ils(tarefas, n_maquinas, ils_max=50, tempo_limite=30, seed=42)
    relatorio(tarefas, n_maquinas, resultado)