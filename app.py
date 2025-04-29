import flet as ft
import json
import os
import subprocess

# Caminho do arquivo JSON
json_file_path = "app.json"
output_dir = "output"

def main(page: ft.Page):
    page.vertical_alignment = ft.MainAxisAlignment.START
    file_list_view = ft.ListView(expand=1, spacing=1)
    
    # Ler o arquivo JSON
    try:
        with open(json_file_path, "r", encoding="utf-8") as file:
            config = json.load(file)
    except Exception as e:
        page.add(ft.Text(f"Erro ao ler o JSON: {e}", color="red"))
        return

    page.title = config.get("page", "Aplicativo Flet para coletar leads do Google Maps")
    
    input_fields = {}
    list_view = ft.ListView(expand=1, spacing=10)

    # Carregar e exibir conteúdo do arquivo filter.txt
    file_path = "filter.txt"
    
    alerta = ft.AlertDialog(
        modal=True,
        title=ft.Text("Aviso"),
        content=ft.Text("A quantidade de termos e velocidade de internet implica no tempo de resposta. Evite repetir muitas vezes a mesma pesquisa."),
        actions=[ft.TextButton("OK", on_click=lambda e: fechar_alerta())],
    )

    def fechar_alerta():
        alerta.open = False
        page.update()

    
    # Função para carregar os arquivos do diretório de saída
    def load_output_files():
        file_list_view.controls.clear()
        if os.path.exists(output_dir):
            files = [f for f in os.listdir(output_dir) if f.endswith(('.csv', '.xlsx'))]
            for file in files:
                file_name, file_extension = os.path.splitext(file)  # Divide o nome e a extensão do arquivo
                file_list_view.controls.append(ft.Row([
                    ft.Text(file_name, expand=True),  # Nome do arquivo
                    ft.Text(file_extension, style="italic", color="gray"),  # Extensão do arquivo em itálico
                    ft.IconButton(icon=ft.icons.DOWNLOAD, on_click=lambda e, file=file: download_file(file)),
                    ft.IconButton(icon=ft.icons.DELETE, on_click=lambda e, file=file: delete_file(file)),
                ]))
        page.update()

    # Função para fazer o download do arquivo
    def download_file(file):
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            page.snack_bar = ft.SnackBar(ft.Text(f"Baixando {file}..."))
            page.snack_bar.open = True
            page.update()
            
            page.launch_url(f"file://{os.path.abspath(file_path)}")
            
    
    # Função para excluir o arquivo
    def delete_file(file):
        file_path = os.path.join(output_dir, file)
        if os.path.exists(file_path):
            os.remove(file_path)
            load_output_files()  # Atualiza a lista após a exclusão
            page.snack_bar = ft.SnackBar(ft.Text(f"Arquivo {file} excluído com sucesso!"))
            page.snack_bar.open = True
            page.update()
    
    def load_file():
        list_view.controls.clear()
        if os.path.exists(file_path):
            with open(file_path, "r") as file:
                lines = file.readlines()
                for index, line in enumerate(lines):
                    list_view.controls.append(ft.Row([
                        ft.Text(line.strip(), expand=True),
                        ft.IconButton(icon=ft.icons.DELETE, on_click=lambda e, i=index: delete_line(i))
                    ]))
        page.update()

    # Função para salvar os dados no arquivo
    def save_fields_to_file(e):
        data = [input_fields[name].value for name in input_fields]
        if all(data):
            with open(file_path, "a") as file:
                file.write(" ".join(data) + "\n")
            load_file()
            for field in input_fields.values():
                if field.name == "pais":
                    field.value = "Brasil"
                # field.value = ""
        else:
            snack_bar = ft.SnackBar(ft.Text("Preencha todos os campos!"))
            page.overlay.append(snack_bar)
            snack_bar.open = True
        page.update()

    # Função para executar o script Python externo
    def run_script(e):
        
        # Botão que dispara a mensagem
        # page.dialog = alerta
        page.overlay.append(alerta)
        alerta.open = True
        page.update()
        
        try:
            subprocess.run(["python", "get_maps_leads.py"], check=True)
            page.snack_bar = ft.SnackBar(ft.Text("Extração de leads executada com sucesso!"))
        except subprocess.CalledProcessError as error:
            page.snack_bar = ft.SnackBar(ft.Text(f"Erro ao executar: {error}"))
        page.snack_bar.open = True
        page.update()

    # Função para deletar uma linha específica do arquivo
    def delete_line(index):
        with open(file_path, "r") as file:
            lines = file.readlines()
        with open(file_path, "w") as file:
            for i, line in enumerate(lines):
                if i != index:
                    file.write(line)
        load_file()


    # Criar os widgets dinamicamente com base no JSON
    row_controls = []
    for field in config.get("fields", []):
        if field["type"] == "string":
            # Calcular a largura proporcional com base no campo "size"
            width = field.get("size", 150)  # Use 150 como padrão se "size" não estiver no JSON
            text_field = ft.TextField(
                label=field["label"],
                hint_text=field.get("placeholder", ""),
                # width=width,
                expand=True
            )
            if field["name"] == "pais":
                text_field.value = "Brasil"
            input_fields[field["name"]] = text_field
            row_controls.append(text_field)
        elif field["type"] == "button" and field["label"] == "Salvar":
            button = ft.ElevatedButton(
                text=field["label"],
                on_click=save_fields_to_file
            )
            row_controls.append(button)

    # Organizar os controles em duas colunas após o Divider
    row_controls_right = [ft.Text("Entradas Salvas:"), list_view]  # Coluna da ListView
    controls_left = [ft.Column(controls=[*row_controls])]  # Coluna com os campos de entrada

    # Ajuste para a linha responsiva
    responsive_row = ft.ResponsiveRow(
        controls=[
            ft.Container(
                col={'xs': 12, 'sm': 6},  # Primeira coluna (campo e botão)
                content=ft.Column(controls=row_controls)
            ),
            ft.Container(
                col={'xs': 12, 'sm': 6},  # Segunda coluna (ListView)
                content=ft.Column(controls=row_controls_right)
            )
        ],
        vertical_alignment=ft.CrossAxisAlignment.START,  # Alinha ao topo
        spacing=10,
        run_spacing=10
    )

    # Adicionando ao page
    page.add(responsive_row)

    # Divisor horizontal
    page.add(ft.Divider())

    # Adiciona o botão "Executar Script" logo abaixo da linha
    run_button = ft.ElevatedButton(
        text="Executar Script",
        on_click=run_script
    )
    page.add(run_button)
    
    
    # Adiciona o conteúdo da lista de arquivos gerados
    page.add(ft.Column([ft.Text("Arquivos Gerados:"), file_list_view]))

    # Carrega os arquivos e exibe o conteúdo
    load_output_files()
    
    # Carrega o arquivo e exibe o conteúdo
    load_file()

# Executa o aplicativo Flet
ft.app(target=main)
