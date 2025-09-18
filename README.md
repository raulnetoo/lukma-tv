# Lukma TV Corporativa

TV corporativa em Streamlit com painel admin e autenticação. Dados no Google Sheets.

## Módulos
- A: Notícias (carrossel 10s, imagem responsiva)
- B: Previsão (usada pelo ticker F)
- C: Aniversariantes (GIF confete, loop)
- D: Vídeos (playlist com duração por item)
- E: Horas mundiais + Cotações (USD, EUR, BTC, ETH → BRL)
- F: **Ticker** rolante de previsão do tempo

## Permissões
- Admin cria usuários e define flags por módulo.
- Usuário comum só edita o que está liberado.

## Execução
```bash
pip install -r requirements.txt
streamlit run app/tv.py
