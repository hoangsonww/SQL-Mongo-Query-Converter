"""
Tests for benchmark utilities.
"""

import pytest
import time
from sql_mongo_converter.benchmark import ConverterBenchmark, BenchmarkResult
from sql_mongo_converter import sql_to_mongo, mongo_to_sql


class TestBenchmarkResult:
    """Test BenchmarkResult dataclass."""

    def test_benchmark_result_creation(self):
        """Test creating a BenchmarkResult."""
        result = BenchmarkResult(
            operation="test_op",
            iterations=100,
            total_time=1.0,
            mean_time=0.01,
            median_time=0.01,
            min_time=0.008,
            max_time=0.015,
            std_dev=0.002,
            queries_per_second=100.0
        )
        assert result.operation == "test_op"
        assert result.iterations == 100
        assert result.total_time == 1.0

    def test_benchmark_result_str(self):
        """Test BenchmarkResult string representation."""
        result = BenchmarkResult(
            operation="test_op",
            iterations=100,
            total_time=1.0,
            mean_time=0.01,
            median_time=0.01,
            min_time=0.008,
            max_time=0.015,
            std_dev=0.002,
            queries_per_second=100.0
        )
        str_repr = str(result)
        assert "test_op" in str_repr
        assert "100" in str_repr

    def test_benchmark_result_to_dict(self):
        """Test BenchmarkResult to_dict method."""
        result = BenchmarkResult(
            operation="test_op",
            iterations=100,
            total_time=1.0,
            mean_time=0.01,
            median_time=0.01,
            min_time=0.008,
            max_time=0.015,
            std_dev=0.002,
            queries_per_second=100.0
        )
        result_dict = result.to_dict()
        assert result_dict['operation'] == "test_op"
        assert result_dict['iterations'] == 100
        assert result_dict['total_time'] == 1.0


class TestConverterBenchmark:
    """Test ConverterBenchmark class."""

    def test_benchmark_creation(self):
        """Test creating a benchmark instance."""
        benchmark = ConverterBenchmark(warmup_iterations=5)
        assert benchmark.warmup_iterations == 5
        assert len(benchmark.results) == 0

    def test_benchmark_simple_function(self):
        """Test benchmarking a simple function."""
        def simple_func(x):
            return x * 2

        benchmark = ConverterBenchmark(warmup_iterations=2)
        result = benchmark.benchmark(simple_func, args=(5,), iterations=10)

        assert result.iterations == 10
        assert result.total_time > 0
        assert result.mean_time > 0
        assert result.queries_per_second > 0

    def test_benchmark_sql_to_mongo(self):
        """Test benchmarking SQL to Mongo conversion."""
        benchmark = ConverterBenchmark(warmup_iterations=2)
        result = benchmark.benchmark(
            sql_to_mongo,
            args=("SELECT * FROM users WHERE age > 25",),
            iterations=10,
            operation_name="SQL to Mongo"
        )

        assert result.operation == "SQL to Mongo"
        assert result.iterations == 10
        assert result.total_time > 0

    def test_benchmark_mongo_to_sql(self):
        """Test benchmarking Mongo to SQL conversion."""
        query = {'collection': 'users', 'find': {'age': {'$gt': 25}}}
        benchmark = ConverterBenchmark(warmup_iterations=2)
        result = benchmark.benchmark(
            mongo_to_sql,
            args=(query,),
            iterations=10,
            operation_name="Mongo to SQL"
        )

        assert result.operation == "Mongo to SQL"
        assert result.iterations == 10

    def test_benchmark_sql_to_mongo_batch(self):
        """Test benchmarking multiple SQL queries."""
        queries = [
            "SELECT * FROM users",
            "SELECT name FROM users WHERE age > 25",
            "SELECT * FROM users ORDER BY name LIMIT 10"
        ]
        benchmark = ConverterBenchmark(warmup_iterations=2)
        results = benchmark.benchmark_sql_to_mongo(
            sql_to_mongo,
            queries,
            iterations_per_query=5
        )

        assert len(results) == 3
        for result in results:
            assert result.iterations == 5
            assert result.total_time > 0

    def test_benchmark_mongo_to_sql_batch(self):
        """Test benchmarking multiple Mongo queries."""
        queries = [
            {'collection': 'users', 'find': {}},
            {'collection': 'users', 'find': {'age': {'$gt': 25}}},
            {'collection': 'users', 'find': {}, 'limit': 10}
        ]
        benchmark = ConverterBenchmark(warmup_iterations=2)
        results = benchmark.benchmark_mongo_to_sql(
            mongo_to_sql,
            queries,
            iterations_per_query=5
        )

        assert len(results) == 3
        for result in results:
            assert result.iterations == 5

    def test_get_summary(self):
        """Test getting benchmark summary."""
        benchmark = ConverterBenchmark(warmup_iterations=2)

        # Run a benchmark
        benchmark.benchmark(
            sql_to_mongo,
            args=("SELECT * FROM users",),
            iterations=10
        )

        summary = benchmark.get_summary()
        assert "Benchmark Summary" in summary
        assert "sql_to_mongo" in summary

    def test_get_summary_empty(self):
        """Test getting summary with no results."""
        benchmark = ConverterBenchmark()
        summary = benchmark.get_summary()
        assert "No benchmark results" in summary

    def test_clear_results(self):
        """Test clearing benchmark results."""
        benchmark = ConverterBenchmark(warmup_iterations=2)

        # Run a benchmark
        benchmark.benchmark(
            sql_to_mongo,
            args=("SELECT * FROM users",),
            iterations=10
        )

        assert len(benchmark.results) > 0
        benchmark.clear_results()
        assert len(benchmark.results) == 0

    def test_statistics_calculation(self):
        """Test that statistics are calculated correctly."""
        def variable_time_func():
            """Function with variable execution time."""
            time.sleep(0.001)

        benchmark = ConverterBenchmark(warmup_iterations=1)
        result = benchmark.benchmark(variable_time_func, iterations=10)

        # Check that all statistics are present and reasonable
        assert result.mean_time > 0
        assert result.median_time > 0
        assert result.min_time > 0
        assert result.max_time > 0
        assert result.min_time <= result.mean_time <= result.max_time
        assert result.std_dev >= 0


class TestBenchmarkIntegration:
    """Integration tests for benchmarking."""

    def test_compare_conversion_performance(self):
        """Test comparing SQL->Mongo vs Mongo->SQL performance."""
        benchmark = ConverterBenchmark(warmup_iterations=2)

        # Benchmark SQL to Mongo
        sql_result = benchmark.benchmark(
            sql_to_mongo,
            args=("SELECT * FROM users WHERE age > 25",),
            iterations=50,
            operation_name="SQL→Mongo"
        )

        # Benchmark Mongo to SQL
        mongo_result = benchmark.benchmark(
            mongo_to_sql,
            args=({'collection': 'users', 'find': {'age': {'$gt': 25}}},),
            iterations=50,
            operation_name="Mongo→SQL"
        )

        assert sql_result.iterations == 50
        assert mongo_result.iterations == 50
        assert len(benchmark.results) == 2
