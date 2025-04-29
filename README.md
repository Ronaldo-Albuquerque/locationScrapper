# Scraper de Negócios do Google Maps

Este projeto realiza a coleta automatizada de informações de negócios a partir do Google Maps usando o `Playwright` com Python. Os dados coletados são salvos em arquivos Excel (`.xlsx`) e CSV (`.csv`).

## Pré-requisitos

- Python 3.10 ou superior
- Git (opcional)
- Linux ou WSL no Windows

## Passos para executar

1. Clone o repositório (caso ainda não tenha feito):

```bash
git clone <URL-do-repositório>
cd <nome-do-repositório>
```

2. Crie e ative um ambiente virtual:
```bash
python -m venv .venv
source .venv/bin/activate
```

3. Instale as dependências necessárias:
```bash
pip install playwright pandas openpyxl
pip install flet
```
> Nota: Caso deseje salvar suas dependências para uso posterior, execute:
> ```bash
> pip freeze > requirements.txt
> ```

4. Instale o navegador Chromium necessário para o Playwright:
```bash
playwright install chromium
```
5. Execute o script principal:
```bash
python app.py
```

# Sobre os dados de entrada
Você pode:
- Passar um termo de busca diretamente pela linha de comando com -s (em desenvolvimento), exemplo:

```bash
python maps_scraper.py -s "restaurantes em São Paulo"
```
- Ou adicionar vários termos ao arquivo `filter.txt`, um por linha. O script os processará automaticamente.

# Saída
Os arquivos de resultado são salvos na pasta output/ nos formatos:

- `search_<termo>.xlsx`
- `search_<termo>.csv`

# Licença
Este projeto é livre para uso educacional e pessoal. Para usos comerciais, entre em contato. [ronaldo.aa@gmail.com](ronaldo.aa@gmail.com)