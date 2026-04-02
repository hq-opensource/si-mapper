#!/usr/bin/env python3

import argparse
from rdflib import Graph, RDF, RDFS, Namespace
import rdflib
from rich.tree import Tree
from rich import print
import sys
import os
import pandas as pd
import pyshacl


def get_prefixes(g: Graph):
    return "\n".join(f"PREFIX {prefix}: <{namespace}>" for prefix, namespace in g.namespace_manager.namespaces())


def get_subclass_hierarchy(g, class_uri):
    query = f"""
    SELECT ?subclass ?parent
    WHERE {{
        ?subclass rdfs:subClassOf+ {class_uri} .
        ?subclass rdfs:subClassOf ?parent .
        FILTER (?parent != ?subclass)
    }}
    """
    results = g.query(query)
    return results



def build_tree(g, class_uri, subclass_data):
    # Extract the local name of the class URI
    local_name = class_uri.split(':')[-1]
    tree = Tree(f"[bold]{local_name}[/bold]")
    children = {}
    
    for row in subclass_data:
        subclass = g.namespace_manager.compute_qname(row.subclass)[2]
        parent = g.namespace_manager.compute_qname(row.parent)[2]
        if parent not in children:
            children[parent] = []
        children[parent].append(subclass)
    
    def add_children(node, parent):
        if parent in children:
            for child in sorted(children[parent]):
                child_node = node.add(f"[white]{child}[/white]")
                add_children(child_node, child)
    
    add_children(tree, local_name)
    return tree


def convert_to_prefixed(uri, g: Graph):
    try:
        prefix, uri_ref, local_name = g.compute_qname(uri)
        return f"{prefix}:{local_name}"
    except Exception as e:
        print(e)
        return uri


def query_to_df(query, g: Graph):
    results = g.query(query)
    formatted_results = [
        [convert_to_prefixed(value, g) if isinstance(value, (str, bytes)) and value.startswith("http") else str(value) for value in row]
        for row in results
    ]
    df = pd.DataFrame(formatted_results, columns=[str(var) for var in results.vars])
    return df


def parse_ttl_files_in_directory(directory_path, g):
    # Iterate through all files in the directory
    for file_name in os.listdir(directory_path):
        # Process only .ttl files
        if file_name.endswith(".ttl"):
            file_path = os.path.join(directory_path, file_name)
            print(f"Processing file: {file_name}")
            # Parse the .ttl file
            try:
                g.parse(file_path, format="turtle")
                # print(f"Parsed {len(g)} triples from {file_name}")
                
            except Exception as e:
                print(f"Error parsing {file_name}: {e}")


def show_subclass_hierarchy(directories, class_uri):
    """
    Load TTL files from directories and show the subclass hierarchy for the given class URI.
    """
    graph = Graph()
    
    # Parse TTL files from all specified directories
    for directory in directories:
        parse_ttl_files_in_directory(directory, graph)
    # Get the subclass hierarchy
    results = get_subclass_hierarchy(graph, class_uri)
    
    # Build and print the tree
    tree = build_tree(graph, class_uri, results)
    print(tree)


def list_classes(directories):
    """
    Load TTL files from directories and list all classes.
    """
    graph = Graph()
    
    # Parse TTL files from all specified directories
    for directory in directories:
        parse_ttl_files_in_directory(directory, graph)
    
    # Query for all classes
    prefixes = get_prefixes(graph)
    query = """
    %s
    SELECT DISTINCT ?class
    WHERE {
        ?class a rdfs:Class .
    }
    ORDER BY ?class
    """ % prefixes
    
    results = graph.query(query)
    
    print("Available classes:")
    for row in results:
        class_uri = row[0]  # Access the first column of the result
        try:
            prefixed = graph.namespace_manager.compute_qname(class_uri)
            print(f"{prefixed[0]}:{prefixed[2]}")
        except:
            print(class_uri)


def run_query(directories, query_str, output_format='table'):
    """
    Load TTL files from directories and run a SPARQL query.
    """
    graph = Graph()
    
    # Parse TTL files from all specified directories
    for directory in directories:
        parse_ttl_files_in_directory(directory, graph)
    
    # Run the query
    results = graph.query(query_str)
    
    if output_format == 'csv':
        df = query_to_df(query_str, graph)
        print(df.to_csv(index=False))
    else:  # table format
        df = query_to_df(query_str, graph)
        print(df)


def main():
    parser = argparse.ArgumentParser(description='RDF Utility Functions')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Common arguments for all commands
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument('--directories', '-d', nargs='+', required=True, 
                              help='Directories containing TTL files')
    
    # Subclass hierarchy command
    hierarchy_parser = subparsers.add_parser('hierarchy', parents=[parent_parser],
                                            help='Show subclass hierarchy')
    hierarchy_parser.add_argument('--class-uri', '-c', required=True, 
                                 help='Class URI to get hierarchy for (e.g., s223:Equipment)')
    
    # List classes command
    list_classes_parser = subparsers.add_parser('list-classes', parents=[parent_parser],
                                              help='List all available classes')
    
    # Query command
    query_parser = subparsers.add_parser('query', parents=[parent_parser],
                                       help='Run a SPARQL query')
    query_parser.add_argument('--query', '-q', required=True, 
                            help='SPARQL query to run')
    query_parser.add_argument('--format', '-f', choices=['table', 'csv'], default='table',
                            help='Output format (default: table)')
    
    # Parse command-line arguments
    args = parser.parse_args()
    
    if args.command == 'hierarchy':
        show_subclass_hierarchy(args.directories, args.class_uri)
    elif args.command == 'list-classes':
        list_classes(args.directories)
    elif args.command == 'query':
        run_query(args.directories, args.query, args.format)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
