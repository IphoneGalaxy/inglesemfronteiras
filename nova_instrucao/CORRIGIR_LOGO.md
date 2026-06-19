📋 Instrução: Corrigir Quebra de Linha do Logo na Sidebar
O logo "Inglês Sem Fronteiras" na barra lateral (sidebar) está quebrando em duas linhas. Preciso que ele fique sempre em uma única linha, ajustando o tamanho da fonte ou o espaçamento para caber sem quebrar.

Ação no arquivo CSS (assets/css/style.css ou assets/css/components.css):

Encontre as classes relacionadas ao logo na sidebar (ex: .sidebar-header .logo, .logo, .logo-text).
Remova qualquer propriedade como word-wrap: break-word; ou white-space: normal;.
Force o texto a ficar em uma única linha e garantir que não ultrapasse a borda. Atualize as propriedades para:
.sidebar-header .logo,.logo {    white-space: nowrap;       /* Impede a quebra de linha */    overflow: hidden;          /* Esconde qualquer excesso */    text-overflow: clip;       /* Não adiciona reticências */    font-size: 1.1rem;         /* Tamanho reduzido para garantir que caiba */    font-weight: 700;    text-decoration: none;    display: block;}
Verifique também se a .sidebar ou .sidebar-header não tem um width muito restritivo. Se tiver, garanta que a sidebar tenha min-width: 250px; (ou o valor que estiver usando) para acomodar o texto.
Faça essa alteração e salve o arquivo. Não é necessário alterar o HTML, apenas o CSS.