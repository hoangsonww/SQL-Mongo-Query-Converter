"""
Performance benchmarking utilities for SQL-Mongo Query Converter.

Provides tools to measure and analyze conversion performance.
"""

import time
import statistics
from typing import Callable, List, Dict, Any, Optional
from dataclasses import dataclass
from .logger import get_logger

logger = get_logger(__name__)


@dataclass
class BenchmarkResult:
    """Container for benchmark results."""

    operation: str
    iterations: int
    total_time: float
    mean_time: float
    median_time: float
    min_time: float
    max_time: float
    std_dev: float
    queries_per_second: float

    def __str__(self) -> str:
        """Return a formatted string representation."""
        return (
            f"\nBenchmark Results for: {self.operation}\n"
            f"{'=' * 50}\n"
            f"Iterations: {self.iterations}\n"
            f"Total Time: {self.total_time:.4f}s\n"
            f"Mean Time: {self.mean_time:.6f}s\n"
            f"Median Time: {self.median_time:.6f}s\n"
            f"Min Time: {self.min_time:.6f}s\n"
            f"Max Time: {self.max_time:.6f}s\n"
            f"Std Dev: {self.std_dev:.6f}s\n"
            f"Throughput: {self.queries_per_second:.2f} queries/sec\n"
            f"{'=' * 50}\n"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'operation': self.operation,
            'iterations': self.iterations,
            'total_time': self.total_time,
            'mean_time': self.mean_time,
            'median_time': self.median_time,
            'min_time': self.min_time,
            'max_time': self.max_time,
            'std_dev': self.std_dev,
            'queries_per_second': self.queries_per_second
        }


class ConverterBenchmark:
    """Benchmark utility for converter operations."""

    def __init__(self, warmup_iterations: int = 10):
        """
        Initialize the benchmark utility.

        Args:
            warmup_iterations: Number of warmup iterations before benchmarking
        """
        self.warmup_iterations = warmup_iterations
        self.results: List[BenchmarkResult] = []

    def benchmark(
        self,
        func: Callable,
        args: tuple = (),
        kwargs: Optional[Dict] = None,
        iterations: int = 100,
        operation_name: Optional[str] = None
    ) -> BenchmarkResult:
        """
        Benchmark a function.

        Args:
            func: Function to benchmark
            args: Positional arguments for the function
            kwargs: Keyword arguments for the function
            iterations: Number of iterations to run
            operation_name: Name of the operation being benchmarked

        Returns:
            BenchmarkResult object
        """
        if kwargs is None:
            kwargs = {}

        if operation_name is None:
            operation_name = func.__name__

        logger.info(f"Starting benchmark: {operation_name}")

        # Warmup
        logger.debug(f"Running {self.warmup_iterations} warmup iterations...")
        for _ in range(self.warmup_iterations):
            func(*args, **kwargs)

        # Actual benchmark
        times: List[float] = []
        logger.debug(f"Running {iterations} benchmark iterations...")

        start_total = time.perf_counter()
        for _ in range(iterations):
            start = time.perf_counter()
            func(*args, **kwargs)
            end = time.perf_counter()
            times.append(end - start)
        end_total = time.perf_counter()

        total_time = end_total - start_total

        # Calculate statistics
        result = BenchmarkResult(
            operation=operation_name,
            iterations=iterations,
            total_time=total_time,
            mean_time=statistics.mean(times),
            median_time=statistics.median(times),
            min_time=min(times),
            max_time=max(times),
            std_dev=statistics.stdev(times) if len(times) > 1 else 0.0,
            queries_per_second=iterations / total_time
        )

        self.results.append(result)
        logger.info(f"Benchmark completed: {operation_name}")
        logger.debug(str(result))

        return result

    def benchmark_sql_to_mongo(
        self,
        converter_func: Callable,
        sql_queries: List[str],
        iterations_per_query: int = 100
    ) -> List[BenchmarkResult]:
        """
        Benchmark SQL to MongoDB conversion.

        Args:
            converter_func: SQL to MongoDB converter function
            sql_queries: List of SQL queries to benchmark
            iterations_per_query: Number of iterations per query

        Returns:
            List of BenchmarkResult objects
        """
        results = []
        for i, query in enumerate(sql_queries):
            result = self.benchmark(
                converter_func,
                args=(query,),
                iterations=iterations_per_query,
                operation_name=f"SQL→Mongo Query {i+1}"
            )
            results.append(result)
        return results

    def benchmark_mongo_to_sql(
        self,
        converter_func: Callable,
        mongo_queries: List[Dict],
        iterations_per_query: int = 100
    ) -> List[BenchmarkResult]:
        """
        Benchmark MongoDB to SQL conversion.

        Args:
            converter_func: MongoDB to SQL converter function
            mongo_queries: List of MongoDB queries to benchmark
            iterations_per_query: Number of iterations per query

        Returns:
            List of BenchmarkResult objects
        """
        results = []
        for i, query in enumerate(mongo_queries):
            result = self.benchmark(
                converter_func,
                args=(query,),
                iterations=iterations_per_query,
                operation_name=f"Mongo→SQL Query {i+1}"
            )
            results.append(result)
        return results

    def get_summary(self) -> str:
        """
        Get a summary of all benchmark results.

        Returns:
            Formatted summary string
        """
        if not self.results:
            return "No benchmark results available."

        summary = "\nBenchmark Summary\n" + "=" * 70 + "\n"
        for result in self.results:
            summary += f"{result.operation:40} {result.queries_per_second:>10.2f} q/s "
            summary += f"(mean: {result.mean_time*1000:>8.3f}ms)\n"
        summary += "=" * 70 + "\n"

        return summary

    def clear_results(self):
        """Clear all benchmark results."""
        self.results.clear()
        logger.debug("Benchmark results cleared")
