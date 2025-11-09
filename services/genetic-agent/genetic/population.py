"""Genetic Programming population management for code repair."""

import random
from typing import List, Dict, Any, Tuple
from dataclasses import dataclass

from .gp_operators import GPOperators


@dataclass
class GPIndividual:
    """Represents an individual in the GP population."""
    ast_tree: Any  # ast.AST
    code: str
    fitness: float = 0.0
    fitness_components: Dict[str, float] = None

    def __post_init__(self):
        if self.fitness_components is None:
            self.fitness_components = {}


class GPPopulation:
    """Manages a population of GP individuals for code repair."""

    def __init__(self,
                 operators: GPOperators,
                 population_size: int = 10,
                 elite_size: int = 2,
                 tournament_size: int = 3):
        self.operators = operators
        self.population_size = population_size
        self.elite_size = elite_size
        self.tournament_size = tournament_size
        self.population: List[GPIndividual] = []
        self.generation = 0

    def initialize_from_seed(self, seed_code: str, variations: int = 9) -> None:
        """Initialize population from a seed individual with variations."""
        # Create seed individual
        seed_tree = self.operators.code_to_tree(seed_code)
        if seed_tree is None:
            raise ValueError("Invalid seed code")

        seed_individual = GPIndividual(
            ast_tree=seed_tree,
            code=seed_code
        )
        self.population = [seed_individual]

        # Generate variations using GP operators
        for _ in range(variations):
            # Apply random mutations to create variations
            mutated_tree = self._apply_random_mutation(seed_tree)
            if mutated_tree and self.operators.validate_ast(mutated_tree):
                mutated_code = self.operators.tree_to_code(mutated_tree)
                individual = GPIndividual(
                    ast_tree=mutated_tree,
                    code=mutated_code
                )
                self.population.append(individual)

        # Fill remaining slots with additional variations if needed
        while len(self.population) < self.population_size:
            base_tree = random.choice([ind.ast_tree for ind in self.population])
            mutated_tree = self._apply_random_mutation(base_tree)
            if mutated_tree and self.operators.validate_ast(mutated_tree):
                mutated_code = self.operators.tree_to_code(mutated_tree)
                individual = GPIndividual(
                    ast_tree=mutated_tree,
                    code=mutated_code
                )
                self.population.append(individual)

        # Ensure we have exactly population_size individuals
        self.population = self.population[:self.population_size]

    def evaluate_fitness(self, fitness_function) -> None:
        """Evaluate fitness for all individuals in the population."""
        for individual in self.population:
            fitness, components = fitness_function(individual.code)
            individual.fitness = fitness
            individual.fitness_components = components

    def select_parents(self) -> List[GPIndividual]:
        """Select parents for reproduction using tournament selection."""
        parents = []

        # Always preserve elites
        sorted_pop = sorted(self.population, key=lambda x: x.fitness, reverse=True)
        elites = sorted_pop[:self.elite_size]
        parents.extend(elites)

        # Select remaining parents via tournament
        remaining_slots = self.population_size - len(parents)
        for _ in range(remaining_slots):
            winner = self._tournament_selection()
            parents.append(winner)

        return parents

    def create_offspring(self, parents: List[GPIndividual]) -> List[GPIndividual]:
        """Create offspring from selected parents."""
        offspring = []

        # Elitism: copy best individuals directly
        sorted_parents = sorted(parents, key=lambda x: x.fitness, reverse=True)
        offspring.extend(sorted_parents[:self.elite_size])

        # Create remaining offspring through crossover and mutation
        while len(offspring) < self.population_size:
            parent1, parent2 = random.sample(parents, 2)

            # Crossover (60% probability)
            if random.random() < 0.6:
                child1_tree, child2_tree = self.operators.subtree_crossover(
                    parent1.ast_tree, parent2.ast_tree
                )

                # Validate and create individuals
                if self.operators.validate_ast(child1_tree):
                    child1_code = self.operators.tree_to_code(child1_tree)
                    offspring.append(GPIndividual(
                        ast_tree=child1_tree,
                        code=child1_code
                    ))

                if len(offspring) < self.population_size and self.operators.validate_ast(child2_tree):
                    child2_code = self.operators.tree_to_code(child2_tree)
                    offspring.append(GPIndividual(
                        ast_tree=child2_tree,
                        code=child2_code
                    ))
            else:
                # Mutation only
                parent = random.choice(parents)
                child_tree = self._apply_random_mutation(parent.ast_tree)

                if child_tree and self.operators.validate_ast(child_tree):
                    child_code = self.operators.tree_to_code(child_tree)
                    offspring.append(GPIndividual(
                        ast_tree=child_tree,
                        code=child_code
                    ))

        return offspring[:self.population_size]

    def evolve(self, fitness_function) -> bool:
        """Evolve the population for one generation."""
        # Evaluate current fitness
        self.evaluate_fitness(fitness_function)

        # Check termination conditions
        best_fitness = max(ind.fitness for ind in self.population)
        if best_fitness >= 0.8:  # Early stopping threshold
            return False  # Stop evolution

        # Select parents
        parents = self.select_parents()

        # Create offspring
        self.population = self.create_offspring(parents)

        self.generation += 1
        return True  # Continue evolution

    def get_best_individual(self) -> GPIndividual:
        """Get the individual with highest fitness."""
        return max(self.population, key=lambda x: x.fitness)

    def get_statistics(self) -> Dict[str, Any]:
        """Get population statistics."""
        if not self.population:
            return {}

        fitnesses = [ind.fitness for ind in self.population]
        complexities = [self.operators.get_tree_complexity(ind.ast_tree) for ind in self.population]

        return {
            "generation": self.generation,
            "population_size": len(self.population),
            "best_fitness": max(fitnesses),
            "avg_fitness": sum(fitnesses) / len(fitnesses),
            "worst_fitness": min(fitnesses),
            "avg_complexity": sum(complexities) / len(complexities),
            "max_complexity": max(complexities)
        }

    def _tournament_selection(self) -> GPIndividual:
        """Perform tournament selection."""
        tournament = random.sample(self.population, min(self.tournament_size, len(self.population)))
        return max(tournament, key=lambda x: x.fitness)

    def _apply_random_mutation(self, tree: Any) -> Any:
        """Apply a random mutation operator using research-based GP operators."""
        # Use the new AST-safe mutation method from research integration
        return self.operators.ast_safe_mutation(tree)