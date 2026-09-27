"""
Iterated Local Search (ILS) para o Problema de Máquinas Paralelas NÃO Idênticas
--------------------------------------------------------------------------------
Instância: 50 tarefas, 6 máquinas com capacidades de processamento diferentes.
Objetivo: minimizar o makespan (Cmax) = tempo em que a última máquina termina.

Modelagem da capacidade: a capacidade de uma máquina funciona como sua
"velocidade". O tempo REAL que uma tarefa leva ao ser executada na máquina m é:

    tempo_real(tarefa, m) = tempo_processamento(tarefa) / capacidade(m)

Ou seja, quanto maior a capacidade da máquina, mais rápido ela executa
qualquer tarefa. A carga (tempo total) de uma máquina é a soma desses
tempos reais das tarefas nela alocadas, e o makespan é o maior valor de
carga entre as 6 máquinas.

Lê os dados do arquivo "dados_maquinas_paralelas_medio.txt" 
"""

import re
import time
import random
from pathlib import Path

def ler_instancia(caminho):
    texto = Path(caminho).read_text(encoding="utf-8")

    n_maquinas = int(re.search(r"Número de máquinas:\s*(\d+)", texto).group(1))

    bloco_capacidades = re.search(
        r"TABELA DE CAPACIDADES.*?\n(.*?)\n-{5,}", texto, re.S
    ).group(1)
    capacidades_dict = {}
    for linha in bloco_capacidades.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s*$", linha)
        if m:
            capacidades_dict[int(m.group(1))] = int(m.group(2))
    capacidades = [capacidades_dict[i] for i in sorted(capacidades_dict)]

    bloco_tarefas = re.search(
        r"TABELA DE TAREFAS.*?\n(.*?)\n-{5,}", texto, re.S
    ).group(1)
    tarefas = {}
    for linha in bloco_tarefas.splitlines():
        m = re.match(r"\s*(\d+)\s+(\d+)\s*$", linha)
        if m:
            tid, tempo = int(m.group(1)), int(m.group(2))
            tarefas[tid] = tempo

    return tarefas, n_maquinas, capacidades

def makespan(atribuicao, tarefas, n_maquinas, capacidades):
    carga = [0.0] * n_maquinas
    for t, m in atribuicao.items():
        carga[m] += tarefas[t] / capacidades[m]
    return max(carga), carga

def construcao_gulosa(tarefas, n_maquinas, capacidades):
    ordem = sorted(tarefas, key=lambda t: -tarefas[t])  
    carga = [0.0] * n_maquinas
    atribuicao = {}
    for t in ordem:
        m = min(range(n_maquinas), key=lambda i: carga[i] + tarefas[t] / capacidades[i])
        atribuicao[t] = m
        carga[m] += tarefas[t] / capacidades[m]
    return atribuicao

def busca_local(atribuicao, tarefas, n_maquinas, capacidades, max_varreduras=100):
    atual = dict(atribuicao)
    custo_atual, _ = makespan(atual, tarefas, n_maquinas, capacidades)

    for _ in range(max_varreduras):
        melhor_move, melhor_custo = None, custo_atual
        for t in tarefas:
            m_original = atual[t]
            for m in range(n_maquinas):
                if m == m_original:
                    continue
                teste = atual.copy()
                teste[t] = m
                custo, _ = makespan(teste, tarefas, n_maquinas, capacidades)
                if custo < melhor_custo - 1e-9:
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

def ils(tarefas, n_maquinas, capacidades, ils_max=50, tempo_limite=60, seed=42):
    rng = random.Random(seed)
    t0 = time.time()

    s0 = construcao_gulosa(tarefas, n_maquinas, capacidades)
    s, custo = busca_local(s0, tarefas, n_maquinas, capacidades)

    historico = [custo]
    iteracao, melhor_iteracao, nivel = 0, 0, 1
    nivel_max = max(2, len(tarefas) // 4)

    while iteracao - melhor_iteracao < ils_max:
        iteracao += 1

        s_linha = perturbacao(s, nivel + 1, n_maquinas, rng)
        s_2linhas, custo_2linhas = busca_local(s_linha, tarefas, n_maquinas, capacidades)

        if custo_2linhas < custo - 1e-9:
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

def relatorio(tarefas, n_maquinas, capacidades, resultado):
    atribuicao = resultado["atribuicao"]
    _, cargas = makespan(atribuicao, tarefas, n_maquinas, capacidades)

    maquinas = {m: [] for m in range(n_maquinas)}
    for t, m in atribuicao.items():
        maquinas[m].append(t)

    print("=" * 70)
    print("RELATÓRIO - PROBLEMA DE MÁQUINAS PARALELAS (INSTÂNCIA MÉDIA)")
    print("=" * 70)
    print(f"Nº de tarefas: {len(tarefas)} | Nº de máquinas: {n_maquinas}\n")

    print("a) Atribuição final de tarefas às máquinas:")
    for m in range(n_maquinas):
        print(f"   Máquina {m + 1} (capacidade {capacidades[m]}): "
              f"tarefas {sorted(maquinas[m])} -> carga (tempo real) = {cargas[m]:.3f}")

    print(f"\nb) Valor final do makespan (Cmax): {resultado['makespan']:.3f}")

    print(f"\nc) Tempo de execução do algoritmo: "
          f"{resultado['tempo_execucao']:.4f} segundos "
          f"({resultado['iteracoes']} iterações do ILS)")

    hist = resultado["historico"]
    print(f"\nd) Evolução do makespan ao longo das iterações do ILS:")
    print(f"   Início (após 1ª busca local): {hist[0]:.3f}")
    print(f"   Fim (melhor solução encontrada): {hist[-1]:.3f}")
    print(f"   Histórico completo: {[round(h, 3) for h in hist]}")

if __name__ == "__main__":
    caminho_dados = Path(__file__).parent / "dados_maquinas_paralelas_medio.txt"

    tarefas, n_maquinas, capacidades = ler_instancia(caminho_dados)
    resultado = ils(tarefas, n_maquinas, capacidades, ils_max=50, tempo_limite=60, seed=42)
    relatorio(tarefas, n_maquinas, capacidades, resultado)