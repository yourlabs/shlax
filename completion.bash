#!/usr/bin/bash

_action(){
  COMPREPLY=()
  cur=${COMP_WORDS[COMP_CWORD]}
  if [[ "$COMP_CWORD" -eq 1  ]] ; then  
      COMPREPLY=($(compgen -W "$(ls shlax/repo/*.py | sed s/^.*\\/\// | cut -d "." -f 1)" "${cur}"))
  else
    action=$(grep "^[^ #)]\w* =" shlax/repo/${COMP_WORDS[1]}.py | cut -d " " -f 1)
    COMPREPLY=($(compgen -W "$action" "${cur}"))
  fi
}

complete -F _action shlax
