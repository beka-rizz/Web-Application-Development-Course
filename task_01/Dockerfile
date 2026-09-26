FROM node:22-alpine

WORKDIR /app

ENV NODE_ENV=production \
    PORT=3000 \
    TZ=Asia/Almaty \
    APP_TITLE="Almaty Time"

COPY --chown=node:node package.json server.js ./

USER node

EXPOSE 3000

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:' + process.env.PORT + '/health').then((res) => process.exit(res.ok ? 0 : 1)).catch(() => process.exit(1))"

CMD ["node", "server.js"]
