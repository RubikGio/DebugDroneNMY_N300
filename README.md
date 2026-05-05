# DebugDroneNMY_N300
Debug del protocollo di comunicazione del drone NMY_N300 la cui comunicazione è tra drone e cellulare.

# Analisi di come arrivare al debug
La scelta per svolgere il debug è stata considerare l'applicazione ` Rx_Drone ` recuperare l'APK e con un decompilatore estrarre tutto il codice. A quel punto avendo poche informazioni a riguardo sulla comunicazione tra drone e cellulare quali l'IP del drone, i primi byte di telemetria del drone, la porta sul quale si instaurava la comunicazione, ho semplicemente preso il codice Java e utilizzato un agente AI per incrociare i pochi dati e trovare gli spezzoni di codice dove era presente la comunicazione sia drone-cellulare ma anche quella contraria. A questo punto il debug si è ridotto alla lettura di tante funzioni offuscate ma e poco leggibili ma che grazie sempre alle AI sono riuscito a decifrare e a farmi un'idea della comunicazione 

# Analisi 
