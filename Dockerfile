# Spy Cadet classroom server: the game plus the school-safe message relay. See README, "Team games at school".
# Run ONE copy only: rooms live in memory, so every device in a class must reach the same server process.
FROM node:22-alpine
WORKDIR /app
COPY server ./server
COPY game ./game
ENV PORT=8080
EXPOSE 8080
USER node
CMD ["node", "server/relay.js"]
