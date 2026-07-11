# maboss_mcp: MCP server over MaBoSS. Based on the project's backend image, which
# already ships pyMaBoSS + the compiled MaBoSS engine. Only the MCP SDK is added.
FROM rg.fr-par.scw.cloud/mabossdemo/backend:v15

# mcp = the MCP SDK ; mpbn = Most-Permissive Boolean Networks (attractors, from a
# MaBoSS model via maboss.to_minibn). Both pip-installable in the slim image.
RUN pip install --no-cache-dir "mcp>=1.2" mpbn

COPY server.py /mcp/server.py
WORKDIR /mcp

# stdio transport: the MCP client speaks to the container over stdin/stdout.
ENTRYPOINT ["python", "/mcp/server.py"]
