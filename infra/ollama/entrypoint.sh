#!/bin/sh
# Ollama-Server im Hintergrund starten
ollama serve &
SERVER_PID=$!

# Warten bis der Server bereit ist
echo "Warte auf Ollama..."
until ollama list > /dev/null 2>&1; do
  sleep 1
done
echo "Ollama bereit."

# Modell pullen falls noch nicht vorhanden
MODEL=${OLLAMA_MODEL:-mistral}
if ! ollama list | grep -q "$MODEL"; then
  echo "Lade Modell: $MODEL"
  ollama pull "$MODEL"
  echo "Modell $MODEL geladen."
else
  echo "Modell $MODEL bereits vorhanden."
fi

# Server im Vordergrund halten
wait $SERVER_PID
