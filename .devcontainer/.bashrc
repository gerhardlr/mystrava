# ─────────────────────────────────────────────
#  Colour definitions
# ─────────────────────────────────────────────
blk='\[\033[01;30m\]'
red='\[\033[01;31m\]'
grn='\[\033[01;32m\]'
ylw='\[\033[01;33m\]'
blu='\[\033[01;34m\]'
pur='\[\033[01;35m\]'
cyn='\[\033[01;36m\]'
wht='\[\033[01;37m\]'
clr='\[\033[00m\]'

export TERM=xterm-256color
export CLICOLOR=1

# ─────────────────────────────────────────────
#  Git prompt
# ─────────────────────────────────────────────
git_branch() {
    local branch
    branch=$(git branch --show-current 2>/dev/null)
    [ -n "$branch" ] && printf " (%s)" "$branch"
}

git_dirty() {
    # Returns * if there are uncommitted changes, + if staged
    local status
    status=$(git status --porcelain 2>/dev/null)
    [ -n "$status" ] && printf "*"
}

# Prompt: user@host:~/dir (branch*) $
PS1="${grn}\u@\h${clr}:${blu}\w${clr}${ylw}\$(git_branch)\$(git_dirty)${clr} \$ "

# ─────────────────────────────────────────────
#  History
# ─────────────────────────────────────────────
HISTSIZE=10000
HISTFILESIZE=20000
HISTTIMEFORMAT="%F %T  "
HISTCONTROL=ignoreboth:erasedups
shopt -s histappend
# Save history after every command
PROMPT_COMMAND="history -a; $PROMPT_COMMAND"

# ─────────────────────────────────────────────
#  Shell options
# ─────────────────────────────────────────────
shopt -s checkwinsize   # update LINES/COLUMNS after each command
shopt -s cdspell        # autocorrect minor cd typos
shopt -s autocd         # type a directory name to cd into it

# ─────────────────────────────────────────────
#  PATH
# ─────────────────────────────────────────────
export PATH="$HOME/.local/bin:$PATH"

# ─────────────────────────────────────────────
#  Navigation aliases
# ─────────────────────────────────────────────
alias ..='cd ..; pwd'
alias ...='cd ../..; pwd'
alias ....='cd ../../..; pwd'

# ─────────────────────────────────────────────
#  ls aliases
# ─────────────────────────────────────────────
alias ls='ls --color=auto'
alias l='ls -CF --color=auto'
alias ll='ls -lhF --color=auto'
alias la='ls -lhAF --color=auto'
alias lt='ls -lhFt --color=auto'   # sort by time

# ─────────────────────────────────────────────
#  General aliases
# ─────────────────────────────────────────────
alias grep='grep --color=auto'
alias c='clear'
alias h='history'
alias hg='history | grep'          # search history: hg <term>
alias mkdir='mkdir -pv'            # create parents, verbose
alias cp='cp -i'                   # confirm before overwrite
alias mv='mv -i'                   # confirm before overwrite
alias df='df -h'
alias du='du -h'
alias free='free -h'

# ─────────────────────────────────────────────
#  Git aliases
# ─────────────────────────────────────────────
alias gs='git status'
alias ga='git add'
alias gaa='git add --all'
alias gc='git commit'
alias gcm='git commit -m'
alias gp='git push'
alias gl='git log --oneline --graph --decorate'
alias gd='git diff'
alias gds='git diff --staged'
alias gb='git branch'
alias gco='git checkout'
alias gcob='git checkout -b'
alias gpl='git pull'
alias gst='git stash'
alias gsp='git stash pop'

# ─────────────────────────────────────────────
#  Python / Poetry
# ─────────────────────────────────────────────
alias py='python'
alias py3='python3'
alias pip='pip3'
alias venv='python3 -m venv .venv && source .venv/bin/activate'
alias activate='source .venv/bin/activate'

# ─────────────────────────────────────────────
#  Useful functions
# ─────────────────────────────────────────────

# Extract any archive
extract() {
    if [ -f "$1" ]; then
        case "$1" in
            *.tar.bz2)  tar xjf "$1"   ;;
            *.tar.gz)   tar xzf "$1"   ;;
            *.tar.xz)   tar xJf "$1"   ;;
            *.bz2)      bunzip2 "$1"   ;;
            *.rar)      unrar x "$1"   ;;
            *.gz)       gunzip "$1"    ;;
            *.tar)      tar xf "$1"    ;;
            *.tbz2)     tar xjf "$1"   ;;
            *.tgz)      tar xzf "$1"   ;;
            *.zip)      unzip "$1"     ;;
            *.Z)        uncompress "$1";;
            *.7z)       7z x "$1"      ;;
            *)          echo "'$1' cannot be extracted via extract()" ;;
        esac
    else
        echo "'$1' is not a valid file"
    fi
}

# Create a directory and cd into it
mkcd() {
    mkdir -p "$1" && cd "$1" || return
}

# Find files by name under current directory
ff() {
    find . -iname "*$1*" 2>/dev/null
}

# Show top 10 largest files/dirs in current directory
biggest() {
    du -ah . 2>/dev/null | sort -rh | head -10
}

# Quick HTTP server in current directory
serve() {
    local port="${1:-8000}"
    echo "Serving on http://localhost:${port}"
    python3 -m http.server "$port"
}
