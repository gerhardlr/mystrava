ARG PYTHON_VERSION=3.12

FROM python:${PYTHON_VERSION}

ARG POETRY_VERSION=1.8.5

# Install Node.js (required for Claude Code) and sudo
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends \
    curl \
    ca-certificates \
    sudo \
    git \
    && curl -fsSL https://deb.nodesource.com/setup_lts.x | bash - \
    && apt-get -y install nodejs \
    && apt-get clean -y && rm -rf /var/lib/apt/lists/*

# Install Claude Code globally
RUN npm install -g @anthropic-ai/claude-code

# Verify Claude Code installation
RUN claude --version || echo "Claude Code installed, authentication required"

# Create vscode user with home directory and add to sudo group
RUN useradd -m -s /bin/bash -G sudo vscode \
    && echo "vscode ALL=(ALL) NOPASSWD:ALL" >> /etc/sudoers.d/vscode \
    && chmod 0440 /etc/sudoers.d/vscode

# Copy .bashrc for vscode user
COPY .bashrc /home/vscode/.bashrc

# Ensure vscode owns their home directory
RUN chown -R vscode:vscode /home/vscode

USER vscode

# Add pipx bin to PATH
ENV PATH="/home/vscode/.local/bin:${PATH}"

# Install pipx, then use it to install Poetry
RUN pip install --no-cache-dir pipx && pipx install poetry==${POETRY_VERSION}

# Configure Poetry to create virtual environments in project directory
RUN poetry config virtualenvs.in-project true

# Create .claude directory
RUN mkdir -p /home/vscode/.claude

WORKDIR /workspace

CMD [ "/bin/bash" ]
