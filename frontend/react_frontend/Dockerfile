# ---- Build Stage ----
FROM node:20-alpine AS builder
WORKDIR /app

# package.json & package-lock.json aus Unterordner kopieren
COPY app/package*.json ./
RUN npm install

# gesamten Next.js Code aus Unterordner kopieren und builden
COPY app ./
RUN npm run build

# ---- Run Stage ----
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production
ENV PORT=3000

# Build-Ergebnisse vom Builder kopieren
COPY --from=builder /app ./

EXPOSE 3000
CMD ["npm", "start"]
