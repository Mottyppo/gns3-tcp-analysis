# Progetto di GNS3 - Analisi Pacchetti TCP

> Ho un'idea così intelligente che la mia testa esploderebbe se solo sapessi di cosa stavo parlando - Peter Griffin

## Introduzione

Il seguente progetto è stato sviluppato per analizzare i pacchetti TCP catturati durante una comunicazione tra due dispositivi e generare un report estensivo dei vari parametri ricavabili. L'output atteso è proprio l'elenco di tutti questi parametri, che possono essere utilizzati in seguito per scrivere una relazione, generare tabelle o grafici. All'interno del codice sono presenti proprio le funzioni per generare tali grafici, ma non sono state implementate per evitare lamentele da parte del professore (ChatGPT o Copilot sono riusciti a generarli identici a quelli forniti nel modello al primo colpo, basta il prompt corretto).

## Get Started

1. Clonare la repository da Github e posizionarsi al suo interno:

   ```sh
   git clone https://github.com/Mottyppo/gns3-tcp-analysis.git
   cd gns3-tcp-analysis/
   ```
2. Creare un virtual environment (venv):

   ```sh
   python -m venv .venv
   ```
3. Attivare il venv:
   * Su Windows:

     ```sh
     .\venv\Scripts\activate
     ```
   * Su macOS/Linux:

     ```sh
     source .venv/bin/activate
     ```
4. Installare i requirements:

   ```sh
   pip install -r requirements.txt
   ```
5. Aggiungere i file `.pcap` alla cartella pcap/ (se non esiste, crearla)
6. Cambiare i propri dati nel file data_analyzer.py, dove sono presenti i commenti TODO

## Utilizzo

Per analizzare i file `.pcap`, eseguire il seguente comando:

```sh
python data_analyzer.py
```

### ATTENZIONE!

In caso i comandi `python` o `pip` non dovessero eseguire correttamente, utilizzare gli alternativi `python3` e `pip3`. Tutte le cartelle dovrebbero così popolarsi correttamente e dovrebbe essere possibile visualizzare da terminale i dati calcolati per i singoli esperimenti

## Credits

Questo progetto è stato sviluppato da [Mottyppo](https://github.com/Mottyppo) 🔥🔥. Se ci sono errori nei calcoli o nelle formule utilizzate ditemelo BESTIA CANE, così li correggo 😘

**P.S.** mettete like alla repository ★