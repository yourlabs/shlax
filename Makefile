all:
	@echo -e "\n\033[1;36m    --> Installing the module ...\033[0m\n"
	pip install --user -e .
	@echo -ne "\n\033[1;36m"; \
	read -p "    --> Install autocompletion ?[Y|n] " RESP; \
	echo -e "\n\033[0m"; \
	case "$$RESP" in \
		y*|Y*|"")sudo cp -v completion.bash /usr/share/bash-completion/completions/shlax;; \
		*);; \
	esac;
