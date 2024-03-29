theme = dict(
    cyan='\033[38;5;51m',
    cyan1='\033[38;5;87m',
    cyan2='\033[38;5;123m',
    cyan3='\033[38;5;159m',
    blue='\033[38;5;33m',
    blue1='\033[38;5;69m',
    blue2='\033[38;5;75m',
    blue3='\033[38;5;81m',
    blue4='\033[38;5;111m',
    blue5='\033[38;5;27m',
    green='\033[38;5;10m',
    green1='\033[38;5;2m',
    green2='\033[38;5;46m',
    green3='\033[38;5;47m',
    green4='\033[38;5;48m',
    green5='\033[38;5;118m',
    green6='\033[38;5;119m',
    green7='\033[38;5;120m',
    purple='\033[38;5;5m',
    purple1='\033[38;5;6m',
    purple2='\033[38;5;13m',
    purple3='\033[38;5;164m',
    purple4='\033[38;5;165m',
    purple5='\033[38;5;176m',
    purple6='\033[38;5;145m',
    purple7='\033[38;5;213m',
    purple8='\033[38;5;201m',
    red='\033[38;5;1m',
    red1='\033[38;5;9m',
    red2='\033[38;5;196m',
    red3='\033[38;5;160m',
    red4='\033[38;5;197m',
    red5='\033[38;5;198m',
    red6='\033[38;5;199m',
    yellow='\033[38;5;226m',
    yellow1='\033[38;5;227m',
    yellow2='\033[38;5;226m',
    yellow3='\033[38;5;229m',
    yellow4='\033[38;5;220m',
    yellow5='\033[38;5;230m',
    gray='\033[38;5;250m',
    gray1='\033[38;5;251m',
    gray2='\033[38;5;252m',
    gray3='\033[38;5;253m',
    gray4='\033[38;5;254m',
    gray5='\033[38;5;255m',
    gray6='\033[38;5;249m',
    pink='\033[38;5;197m',
    pink1='\033[38;5;198m',
    pink2='\033[38;5;199m',
    pink3='\033[38;5;200m',
    pink4='\033[38;5;201m',
    pink5='\033[38;5;207m',
    pink6='\033[38;5;213m',
    orange='\033[38;5;202m',
    orange1='\033[38;5;208m',
    orange2='\033[38;5;214m',
    orange3='\033[38;5;220m',
    orange4='\033[38;5;172m',
    orange5='\033[38;5;166m',
    reset='\033[0m',
)


class Colors:
    def __init__(self, **theme):
        for name, value in theme.items():
            setattr(self, name, value)
            setattr(self, f'b{name}', value.replace('[', '[1;'))


c = colors = Colors(**theme)
