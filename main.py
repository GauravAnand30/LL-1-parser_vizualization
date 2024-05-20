import streamlit as st

def remove_left_recursion(grammar):
    productions = grammar.split('\n')
    non_terminals = set()
    productions_dict = {}

    
    for production in productions:
        head, body = production.split('->')
        head = head.strip()
        body = [symbol.strip() for symbol in body.split('|')]
        non_terminals.add(head)
        if head in productions_dict:
            productions_dict[head].extend(body)
        else:
            productions_dict[head] = body

    modified_productions = []

    for non_terminal in non_terminals:
        alphas = []
        betas = []

        
        for production in productions_dict[non_terminal]:
            if production.startswith(non_terminal):
                alphas.append(production[len(non_terminal):])
            else:
                betas.append(production)

        if alphas:
            new_non_terminal = non_terminal + "'"
            modified_productions.append(non_terminal + " -> " + '|'.join([beta + ' ' + new_non_terminal for beta in betas]))
            modified_productions.append(new_non_terminal + " -> " + '|'.join([alpha + ' ' + new_non_terminal for alpha in alphas]) + ' | ε')
        else:
            modified_productions.append(non_terminal + " -> " + '|'.join(betas))

    modified_grammar = '\n'.join(modified_productions)
    return modified_grammar

def compute_first(grammar):
    first = {}
    for non_terminal in grammar:
        first[non_terminal] = set()
    
    # Compute First sets
    for non_terminal in grammar:
        compute_first_recursive(grammar, non_terminal, first)
    
    return first

def compute_first_recursive(grammar, non_terminal, first):
    if len(grammar[non_terminal]) == 0:  # If epsilon production
        first[non_terminal].add('epsilon')
    else:
        for production in grammar[non_terminal]:
            if production[0] not in grammar:  # If terminal
                first[non_terminal].add(production[0])
            else:  # If non-terminal
                if 'epsilon' in first[production[0]]:
                    first[non_terminal] |= first[production[0]]
                    first[non_terminal].remove('epsilon')
                else:
                    first[non_terminal] |= first[production[0]]
                    break

def compute_follow(grammar, start_symbol, first):
    follow = {non_terminal: set() for non_terminal in grammar}
    follow[start_symbol].add('$')  
    
    while True:
        updated = False
        for non_terminal in grammar:
            for production in grammar[non_terminal]:
                for i, symbol in enumerate(production):
                    if symbol in grammar and i < len(production) - 1:  # Non-terminal followed by another symbol
                        for next_symbol in production[i+1:]:
                            if next_symbol not in grammar:  # Terminal
                                follow[symbol].add(next_symbol)
                                break
                            else:  # Non-terminal
                                if 'epsilon' in first[next_symbol]:
                                    follow[symbol] |= first[next_symbol] - {'epsilon'}
                                    if 'epsilon' not in first[next_symbol]:
                                        break
                                else:
                                    follow[symbol] |= first[next_symbol]
                                    break
                        else:  # All next symbols derive epsilon
                            if non_terminal != symbol:  # Avoid left recursion
                                follow[symbol] |= follow[non_terminal]
                    elif symbol in grammar and i == len(production) - 1:  # Last symbol in production
                        follow[symbol] |= follow[non_terminal]
                    else:  # Terminal
                        continue
        
        if not updated:
            break
    
    return follow

def generate_ll1_parse_table(grammar, first_sets, follow_sets):
    parse_table = {}

    for non_terminal in grammar:
        for production in grammar[non_terminal]:
            first_set_of_production = compute_first_of_production(production, first_sets)
            for terminal in first_set_of_production:
                parse_table[(non_terminal, terminal)] = production

            if 'epsilon' in first_set_of_production:
                follow_set_of_non_terminal = follow_sets[non_terminal]
                for terminal in follow_set_of_non_terminal:
                    if (non_terminal, terminal) not in parse_table:
                        parse_table[(non_terminal, terminal)] = production

    return parse_table

def compute_first_of_production(production, first_sets):
    first_set_of_production = set()
    for symbol in production:
        if symbol in first_sets:
            first_set_of_production |= first_sets[symbol]
            if 'epsilon' not in first_sets[symbol]:
                break
        else:
            first_set_of_production.add(symbol)
            break
    return first_set_of_production

def parse_input_string(input_string, ll1_parse_table):
    stack = ['$']
    input_string += '$'  # Add end marker to the input string
    input_index = 0
    output_steps = []

    while stack:
        top_of_stack = stack[-1]
        current_input = input_string[input_index]

        if top_of_stack == current_input:
            stack.pop()
            input_index += 1
            output_steps.append((stack[:], input_string[input_index:]))
        elif (top_of_stack, current_input) in ll1_parse_table:  # Check if there's a valid production for this combination
            production = ll1_parse_table[top_of_stack, current_input]
            stack.pop()
            if production != 'epsilon':
                stack.extend(reversed(production))
            output_steps.append((stack[:], input_string[input_index:]))
        else:
            return False, output_steps

    return True, output_steps


def main():
    st.title("LL(1) PARSER Analysis Tool")
    
    st.markdown("""
    <style>
    body {
        color: orange;
        background-color: white;
    }
    .stButton>button {
        font-weight: bold;
        font-size: 16px;
        padding: 10px 20px;
        background-color: orange;
        color: white;
        animation: button-pulse 1s infinite alternate;
        border-radius: 10px;
        border: none;
        box-shadow: 0px 4px 6px rgba(0, 0, 0, 0.1);
    }
    .stButton>button:hover {
        background-color: #ff7f00; 
    }
    @keyframes button-pulse {
        0% {
            transform: scale(1);
        }
        100% {
            transform: scale(1.05);
        }
    }
    .bold-text {
        font-weight: bold;
    }
    .styled-table {
        border-collapse: collapse;
        margin: 20px 0;
        font-size: 16px;
        min-width: 700px;
        box-shadow: 0 0 20px rgba(0, 0, 0, 0.15);
    }
    .styled-table th,
    .styled-table td {
        padding: 12px 15px;
        text-align: center;
    }
    .styled-table th {
        background-color: orange;
        color: white;
        font-weight: bold;
    }
    .styled-table tr:nth-child(even) {
        background-color: #f2f2f2;
    }
    .styled-table tr:hover {
        background-color: #ddd;
    }
    </style>
    """, unsafe_allow_html=True)


    grammar_input = st.text_area("Enter the grammar (separated by new lines)")
    modified_grammar = None  # Define it here

    if st.button("Remove Left Recursion"):
        modified_grammar = remove_left_recursion(grammar_input)
        st.write("Modified Grammar:")
        st.code(modified_grammar)

        # Parse modified grammar into a dictionary
        modified_grammar_dict = {}
        lines = modified_grammar.split('\n')
        for line in lines:
            non_terminal, production = line.split('->')
            non_terminal = non_terminal.strip()
            production = [symbol.strip() for symbol in production.split('|')]
            modified_grammar_dict[non_terminal] = production

        # Display FIRST and FOLLOW sets for the modified grammar
        first_set_modified = compute_first(modified_grammar_dict)
        follow_set_modified = compute_follow(modified_grammar_dict, list(modified_grammar_dict.keys())[0], first_set_modified)

        # Display FIRST set for the modified grammar
        st.write("FIRST Set (Modified Grammar):")
        for key, value in first_set_modified.items():
            st.write(key, "->", value)

        # Display FOLLOW set for the modified grammar
        st.write("FOLLOW Set (Modified Grammar):")
        for key, value in follow_set_modified.items():
            st.write(key, "->", value)
        
        # Generate LL(1) parsing table
        ll1_parse_table = generate_ll1_parse_table(modified_grammar_dict, first_set_modified, follow_set_modified)

        # Display LL(1) parsing table
        st.write("LL(1) Parsing Table:")
        # Convert parsing table into a list of dictionaries
        ll1_parse_table_data = [{'Non-terminal': key[0], 'Terminal': key[1], 'Production': value} for key, value in ll1_parse_table.items()]
        st.table(ll1_parse_table_data)

        # Input string verification
        input_string = st.text_input("Enter the string to verify:")
        if st.button("Verify"):
            accepted, output_steps = parse_input_string(input_string, ll1_parse_table)
            if accepted:
                st.write("String Accepted!")
            else:
                st.write("String Rejected!")
                st.write("Parsing Steps:")
                for step in output_steps:
                    st.write("Stack:", step[0], "Input:", step[1])

if __name__ == "__main__":
    main()
