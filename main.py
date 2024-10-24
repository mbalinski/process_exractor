 # This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>

import re
import PyPDF2
import networkx as nx
import matplotlib.pyplot as plt

# PDF to text conversion function
def convert_pdf_to_text(pdf_file_path):
    text = ""
    with open(pdf_file_path, 'rb') as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text()
    return text

# Patterns for chapters, articles, and subpoints
chapter_pattern = r'(Rozdział \d+)'
article_pattern = r'(Art\. \d+\.|§ \d+\.)'
subpoint_pattern = r'(\d+\))'

# Process keywords
actions_keywords = [
    "zmiana", "uchyla się", "dodaje się", "wchodzi w życie", "ustawa", "rozporządzenie", "decyzja",
    "wymagania", "procedura", "czynność", "zgoda", "przyjęcie", "wniosek", "wydanie decyzji",
    "zatwierdzenie", "kontrola", "monitorowanie", "przeprowadzenie analizy", "zawieszenie",
    "unieważnienie", "dopuszczenie", "zezwolenie", "przekazanie", "wykonanie", "realizacja",
    "wymóg", "obowiązek", "ustanowienie", "ogłoszenie", "postępowanie", "złożenie sprawozdania"
]

# Time-related keywords
time_patterns = [
    r"(\d{1,2}) dni", r"(\d{1,2}) miesięcy", r"do dnia (\d{1,2})", r"od dnia (\d{1,2})",
    r"po upływie (\d{1,2}) dni", r"po upływie (\d{1,2}) miesięcy", r"z dniem (\d{1,2})",
    "wchodzi w życie", "termin", "okres", "w terminie", "najpóźniej", "przed upływem",
    "po upływie", "do końca roku", "w ciągu", "od dnia", "nie później niż",
    "do końca kwartału", "w przeciągu", "od daty"
]


def extract_title(text):
    title_pattern = r'(Poz\.\s*\d+.*?)(20\d{2})'
    match = re.search(title_pattern, text, re.DOTALL)
    if match:
        title = f"{match.group(1)} {match.group(2)}"
        return title.strip()
    return "Unknown Title"


# Fragment text by chapters, articles, and subpoints with sequence validation
def fragment_text(text):
    chapters = re.split(chapter_pattern, text)
    fragments = []

    current_chapter = None  # Track the current chapter context
    current_article = None  # Track the current article context

    expected_chapter_number = 1  # Start from Rozdział 1
    expected_article_number = 1  # Start from Art. 1.

    for chapter in chapters:
        if chapter.strip():
            chapter_match = re.match(chapter_pattern, chapter)
            if chapter_match:
                # Extract the chapter number
                chapter_number_match = re.search(r'Rozdział (\d+)', chapter_match.group(0))
                if chapter_number_match:
                    chapter_number = int(chapter_number_match.group(1))

                    # Only accept if the chapter is the expected next chapter
                    if chapter_number == expected_chapter_number:
                        current_chapter = chapter_match.group(0)
                        expected_chapter_number += 1  # Increment expected chapter number
                    else:
                        continue  # Skip out-of-sequence chapters

            articles = re.split(article_pattern, chapter)

            for article in articles:
                article_match = re.search(article_pattern, article)
                if article_match:
                    # Extract the article number
                    article_number_match = re.search(r'Art\. (\d+)\.', article_match.group(0))
                    if article_number_match:
                        article_number = int(article_number_match.group(1))

                        # Only accept if the article is the expected next article
                        if article_number == expected_article_number:
                            current_article = article_match.group(0)
                            expected_article_number += 1  # Increment expected article number
                        else:
                            continue  # Skip out-of-sequence articles

                # Ensure the current article is used even if no match found
                if article.strip():
                    subpoints = re.split(subpoint_pattern, article)
                    article_main = subpoints[0].strip() if subpoints else ""

                    processed_subpoints = []

                    # Process subpoints so the numbering (e.g., 1)) is tied to the text that follows
                    i = 1  # Subpoint numbering starts at 1
                    subpoint_text = None

                    for sp in subpoints[1:]:
                        if re.match(subpoint_pattern, sp.strip()):
                            # If the subpoint pattern is found, store the number and reset text
                            if subpoint_text:
                                processed_subpoints.append((f"{current_article}.{i}", subpoint_text.strip()))
                                i += 1
                            subpoint_text = sp.strip()  # Start a new subpoint
                        else:
                            # If the subpoint pattern is not found, it's part of the previous subpoint's text
                            subpoint_text += " " + sp.strip()

                    # Append the last subpoint
                    if subpoint_text:
                        processed_subpoints.append((f"{current_article}.{i}", subpoint_text.strip()))

                    # Add to fragments
                    fragments.append({
                        'chapter': current_chapter,
                        'article_number': current_article if current_article else 'Brak artykułu',
                        'article_main': article_main,
                        'subpoints': processed_subpoints
                    })

    return fragments



# Find processes in the text
def find_processes_in_text(fragments):
    found_processes = []

    for fragment in fragments:
        chapter = fragment['chapter']
        article = fragment['article_number']
        article_main = fragment['article_main']

        # Search processes in the article's main text
        for action_keyword in actions_keywords:
            if re.search(action_keyword, article_main):
                time_match = next((time_pattern for time_pattern in time_patterns if
                                   re.search(time_pattern, article_main)), None)
                found_processes.append({
                    'chapter': chapter,
                    'article_number': article,
                    'subpoint': article_main,
                    'action': action_keyword,
                    'time': time_match if time_match else 'Brak terminu'
                })

                # If the article has no subpoints, add a subpoint X..0
                if not fragment['subpoints']:  # No subpoints exist
                    found_processes.append({
                        'chapter': chapter,
                        'article_number': f"{article}.0",  # Article subpoint X..0
                        'subpoint': "Brak podpunktów, ale proces wykryty",  # Custom message
                        'action': action_keyword,
                        'time': time_match if time_match else 'Brak terminu'
                    })

        # Search processes in each subpoint
        for subpoint_id, subpoint in fragment['subpoints']:
            if subpoint.strip():
                for action_keyword in actions_keywords:
                    if re.search(action_keyword, subpoint):
                        time_match = next(
                            (time_pattern for time_pattern in time_patterns if re.search(time_pattern, subpoint)), None)
                        found_processes.append({
                            'chapter': chapter,
                            'article_number': subpoint_id if article else f"{subpoint_id}",
                            'subpoint': subpoint.strip(),
                            'action': action_keyword,
                            'time': time_match if time_match else 'Brak terminu'
                        })

    return found_processes



def visualize_processes_on_graph(processes, graph_title):
    G = nx.DiGraph()

    chapter_nodes = set()
    article_nodes = set()
    subpoint_nodes = set()

    article_to_subpoints = {}

    # Create the nodes and edges for the graph
    for process in processes:
        chapter = process['chapter']
        article_number = process['article_number'].strip()  # Trim any whitespace
        subpoint = process['subpoint']

        # Extract the hierarchy from the article_number
        chapter_match = re.search(r'(Rozdział \d+)', chapter) if chapter else None
        article_match = re.search(r'(Art\. \d+|§ \d+)', article_number)  # Updated to include '§'
        subpoint_match = re.search(r'\.(\d+)', article_number)

        chapter_node = chapter_match.group(0) if chapter_match else None
        article_node = article_match.group(0) if article_match else None
        subpoint_node = article_number if subpoint_match else None

        # Add nodes and edges based on the hierarchy Rozdział -> Artykuł -> Subpoint
        if chapter_node and article_node:
            G.add_edge(chapter_node, article_node)
            chapter_nodes.add(chapter_node)  # Track chapter nodes for coloring

        if article_node:
            article_nodes.add(article_node)  # Track article nodes for coloring
            # For articles without subpoints, we need to ensure they're added to the graph
            if not subpoint_match:
                subpoint_node = f"{article_node}.0"  # Create a subpoint X..0
                G.add_edge(article_node, subpoint_node)
                subpoint_nodes.add(subpoint_node)  # Ensure the node is registered

        if article_node and subpoint_node:
            G.add_edge(article_node, subpoint_node)
            subpoint_nodes.add(subpoint_node)  # Track subpoint nodes for coloring

            # Track subpoints for each article to sort them later
            if article_node not in article_to_subpoints:
                article_to_subpoints[article_node] = []
            article_to_subpoints[article_node].append(subpoint_node)

    # Sort nodes within each level based on their numerical identifiers
    def sort_nodes(nodes, pattern):
        sorted_list = sorted(nodes, key=lambda x: int(re.search(pattern, x).group(1)) if re.search(pattern, x) else 0)
        return sorted_list

    sorted_chapters = sort_nodes(chapter_nodes, r'Rozdział (\d+)')
    sorted_articles = sort_nodes(article_nodes, r'Art\. (\d+)|§ (\d+)')

    # Sort subpoints for each article
    for article in article_to_subpoints:
        article_to_subpoints[article] = sort_nodes(article_to_subpoints[article], r'\.(\d+)')

    # Assign positions
    pos = {}
    y_spacing = 1  # Base vertical spacing between nodes
    subpoint_spacing = 0.5  # Base spacing between subpoints
    x_positions = {'chapter': 0, 'article': 1, 'subpoint': 2}

    # Position Rozdział
    for i, chapter in enumerate(sorted_chapters):
        pos[chapter] = (x_positions['chapter'], -i * y_spacing)

    # Position Artykuł
    for i, article in enumerate(sorted_articles):
        # Find the parent chapter to align vertically
        parent_chapters = [ch for ch in sorted_chapters if ch in G.predecessors(article)]
        if parent_chapters:
            parent = parent_chapters[0]
            pos[article] = (x_positions['article'], pos[parent][1] - i * y_spacing)  # Align under parent
        else:
            pos[article] = (x_positions['article'], -len(sorted_chapters) * y_spacing - i * y_spacing)  # Default position

        # Position Podpunkt with extra spacing to avoid overlap
        subpoint_index = 0
        for subpoint in article_to_subpoints[article]:
            # Adjust the y-position based on the index of the subpoint
            pos[subpoint] = (x_positions['subpoint'], pos[article][1] - subpoint_index * (subpoint_spacing + 0.3))
            subpoint_index += 1

    # Ensure all nodes have positions before drawing edges
    for node in G.nodes:
        if node not in pos:
            print(f"Warning: Node '{node}' is missing from pos. Assigning default position.")
            pos[node] = (x_positions['article'], 0)  # Default to (1, 0) if position is missing

    # Adjust figure size dynamically based on the number of nodes
    node_count = len(G.nodes())
    plt.figure(figsize=(max(12, node_count * 0.5), max(8, node_count * 0.3)))

    # Draw the graph with color differentiation
    nx.draw_networkx_nodes(G, pos, nodelist=sorted_chapters, node_color="cyan", node_size=3000, label="Rozdział")
    nx.draw_networkx_nodes(G, pos, nodelist=sorted_articles, node_color="lightblue", node_size=2000, label="Artykuł")
    nx.draw_networkx_nodes(G, pos, nodelist=list(subpoint_nodes), node_color="lightgreen", node_size=1500,
                           label="Podpunkt")

    # Draw edges
    nx.draw_networkx_edges(G, pos, edgelist=G.edges(), edge_color="gray")

    # Draw labels
    nx.draw_networkx_labels(G, pos, font_size=10, font_weight='bold')

    plt.title(graph_title)
    plt.axis('off')  # Hide axes
    plt.tight_layout()
    plt.show()

    # Print the count of different nodes
    print(f"Liczba węzłów Rozdział: {len(sorted_chapters)}")
    print(f"Liczba węzłów Artykuł: {len(sorted_articles)}")
    print(f"Liczba węzłów Podpunkt: {len(subpoint_nodes)}")


# Print the found processes
def print_processes(processes):
    for i, process in enumerate(processes, start=1):
        print(f"Proces {i}:")
        print(f"Rozdział: {process['chapter']}")
        print(f"Artykuł: {process['article_number']}")
        print(f"Podpunkt: {process['subpoint']}")
        print(f"Akcja: {process['action']}")
        print(f"Czas: {process['time']}\n")


# Main function to process PDF and visualize processes
def process_pdf(pdf_file_path):
    text = convert_pdf_to_text(pdf_file_path)
    file_title = extract_title(text)
    fragments = fragment_text(text)
    processes = find_processes_in_text(fragments)

    print_processes(processes)
    visualize_processes_on_graph(processes, file_title)


# Test with the provided PDF file
pdf_file_path = 'pdf_files/main_test.pdf'
process_pdf(pdf_file_path)