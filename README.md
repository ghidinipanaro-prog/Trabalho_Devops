# Trabalho_Devops: Projeto Devoops

Orquestração de contêineres em **quatro ambientes** (desenvolvimento, homologação, pré-produção e produção), cada um com **seu próprio pipeline de CI/CD**, implementado em **GitHub Actions** e em **Jenkins**.

## Objetivo

1. Empacotar uma aplicação simples em **contêiner** (Docker).
2. Orquestrar com **Kubernetes**, com um ambiente isolado para cada fase.
3. Criar um **pipeline individual por ambiente**.
4. Documentar todas as etapas: criação dos contêineres, configuração da orquestração e execução dos pipelines.

## Stack

| Peça | Ferramenta |
|---|---|
| Aplicação | Python + Flask (servidor gunicorn) |
| Contêiner | Docker |
| Registry de imagens | GitHub Container Registry (ghcr.io) |
| Orquestração | Kubernetes local com **kind** |
| Separação de ambientes | 1 *namespace* por ambiente + Kustomize (`base` + `overlays`) |
| CI/CD | GitHub Actions (runner self-hosted) e Jenkins |
| Segurança | Scan de vulnerabilidades com Trivy (pré-produção) |

## Ambientes

| Ambiente | Namespace | Réplicas | `APP_ENV` | Origem no GitHub Actions | Pipeline Jenkins |
|---|---|---|---|---|---|
| Desenvolvimento | `dev` | 1 | dev | branch `develop` | `pipeline-dev` |
| Homologação | `hml` | 1 | hml | branch `release` | `pipeline-hml` |
| Pré-produção | `pre` | 2 | pre | branch `main` | `pipeline-pre` |
| Produção | `prod` | 3 | prod | tag `v*` (aprovação manual) | `pipeline-prod` (aprovação manual) |

## Fluxo de CI/CD

```
develop ──push──► Pipeline DEV  ──► namespace dev
release ──push──► Pipeline HML  ──► namespace hml
main    ──push──► Pipeline PRE  ──► namespace pre
tag v*  ──push──► Pipeline PROD ──► namespace prod   (aprovação manual)
```

| Pipeline | Etapas (GitHub Actions) | Etapas (Jenkins) |
|---|---|---|
| DEV | build, deploy | testes, build, deploy |
| HML | testes, build, deploy | promove a imagem do DEV, deploy |
| PRE | testes, build, scan Trivy, publicação, deploy | scan Trivy, promove a imagem do HML, deploy |
| PROD | aprovação manual, deploy da imagem do PRE | aprovação manual, promove a imagem do PRE, deploy |

Em produção a imagem **não é reconstruída**: promove-se a que já passou pelos testes e pelo scan.

## Estrutura do repositório

```
Trabalho_Devops/
├── app/                    # aplicação Flask, requirements e Dockerfile
├── tests/                  # testes automatizados (pytest)
├── k8s/
│   ├── base/               # deployment e service comuns
│   └── overlays/           # dev, hml, pre, prod
├── .github/workflows/      # dev.yml, hml.yml, pre.yml, prod.yml
├── jenkins/                # Dockerfile, compose e Jenkinsfile de cada ambiente
└── docs/                   # documentação detalhada e prints
```

## Documentação

| Documento | Conteúdo |
|---|---|
| [01-arquitetura.md](docs/01-arquitetura.md) | Visão geral, decisões e como os ambientes são separados |
| [02-containers.md](docs/02-containers.md) | Aplicação, Dockerfile linha a linha, build e execução |
| [03-orquestracao.md](docs/03-orquestracao.md) | Cluster kind, namespaces, Kustomize base e overlays |
| [04-pipelines.md](docs/04-pipelines.md) | Os 4 pipelines do GitHub Actions e o runner self-hosted |
| [05-operacao.md](docs/05-operacao.md) | Retomar o ambiente, deploy, promoção, rollback e logs |
| [06-problemas.md](docs/06-problemas.md) | Erros encontrados, causas e soluções |
| [07-jenkins.md](docs/07-jenkins.md) | Jenkins: instalação, credenciais, jobs e pipelines |
| [08-requisitos.md](docs/08-requisitos.md) | Checklist do que foi pedido x o que foi entregue |

## Como reproduzir (resumo)

Pré-requisitos: Git, Docker Desktop, kubectl e kind.

```bash
git clone https://github.com/ghidinipanaro-prog/Trabalho_Devops.git
cd Trabalho_Devops

# 1. imagem local
docker build -t devoops:local ./app

# 2. cluster e ambientes
kind create cluster --name devoops
kubectl create namespace dev
kubectl create namespace hml
kubectl create namespace pre
kubectl create namespace prod

# 3. aplicar um ambiente manualmente
kubectl apply -k k8s/overlays/dev
kubectl get pods -n dev
```

Para ver a aplicação de um ambiente (a porta 8080 é usada pelo Jenkins):

```bash
kubectl port-forward -n dev svc/devoops 8091:80
# abrir http://localhost:8091  ->  {"ambiente":"dev","app":"devoops"}
```

Os pipelines automáticos exigem:
- **GitHub Actions:** runner self-hosted ligado na máquina (veja [04-pipelines.md](docs/04-pipelines.md)).
- **Jenkins:** contêiner `jenkins-devops` no ar, na rede do cluster, com as credenciais configuradas (veja [07-jenkins.md](docs/07-jenkins.md)).

## Operação

```bash
# estado dos ambientes
kubectl get pods -A | grep devoops

# imagem em uso em cada ambiente
for ns in dev hml pre prod; do echo -n "$ns: "; kubectl get deployment devoops -n $ns -o jsonpath='{.spec.template.spec.containers[0].image}'; echo; done

# rollback
kubectl rollout history deployment/devoops -n prod
kubectl rollout undo deployment/devoops -n prod
```

## Observações

- Os quatro ambientes são isolados por *namespace* dentro de **um único cluster** local. Em um cenário real, produção ficaria em um cluster separado.
- GitHub Actions e Jenkins implantam nos mesmos *namespaces*: o último deploy prevalece (detalhes em [07-jenkins.md](docs/07-jenkins.md)).
- Credenciais (kubeconfig, tokens) **não** fazem parte do repositório.

## Autor

Projeto acadêmico de DevOps, desenvolvido por ghidinipanaro-prog.
