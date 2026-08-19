# Graph Report - hydradb  (2026-08-19)

## Corpus Check
- 120 files · ~328,203 words
- Verdict: corpus is large enough that graph structure adds value.

## Summary
- 5867 nodes · 19553 edges · 180 communities (177 shown, 3 thin omitted)
- Extraction: 96% EXTRACTED · 4% INFERRED · 0% AMBIGUOUS · INFERRED: 741 edges (avg confidence: 0.8)
- Token cost: 0 input · 0 output

## Graph Freshness
- Built from commit: `6a2fbb19`
- Run `git rev-parse HEAD` and compare to check if the graph is stale.
- Run `graphify update .` after code changes (no API cost).

## Community Hubs (Navigation)
- Result
- QueryContext
- graph-indexer.rs
- query/path_procedure.rs
- heartbeat.rs
- query_optimizer.rs
- query.rs
- bolt/tests.rs
- ObjectStoreWriterLeaseDirectory
- opencypher.rs
- NamespacePath
- http.rs
- GraphShard
- query_bench.rs
- FaultStore
- meter.rs
- String
- validate_component
- open_test_shard
- state.rs
- properties
- Self
- graphblas.rs
- codec.rs
- Result
- src/tests.rs
- bolt_benchmark.rs
- admin.rs
- CompiledGraphBlasMatrix
- falkor_import.rs
- Result
- ClientQueryService
- Result
- cluster.rs
- GraphStore
- cache.rs
- engine.rs
- GraphTopologyOverlay
- VertexPropertyValue
- properties
- RecordStore
- core/config.rs
- otel_metrics.rs
- Option
- Into
- typed_mutation
- query_correctness.rs
- algebra.rs
- GraphScope
- Option
- liveness.rs
- service/tests.rs
- EdgeMetadata
- write.rs
- GraphCorrectnessReport
- ListFailingStore
- mutation
- falkor_query_bench.rs
- coordination.rs
- service.rs
- .format_event
- VertexMetadata
- .from_values
- src/config.rs
- multigraph_bench.rs
- GraphError
- GraphWriteBatch
- corpus.rs
- VertexId
- GraphIndexGeneration
- NodeHistograms
- Result
- PlacementView
- propagate.rs
- Result
- otlp.rs
- meter_export.rs
- BoltServerConfig
- Self
- enabled
- FailingStore
- .new
- TcpQueryCellClient
- enum
- .should_sample
- placement.rs
- graph-node.rs
- .build_matrix_tiles
- required
- head_sampling.rs
- .compact_out_adjacency_segments_locked
- .deny
- properties
- layers.rs
- properties
- properties
- locality.rs
- Arc
- Option
- .try_execute_graph_kernel_opencypher_rows_page
- tls.rs
- networkPolicyPeer
- properties
- runtime_smoke.sh
- bolt.rs
- model.rs
- corrupt
- properties
- http/tests.rs
- ScopedRoutedGraphCluster
- properties
- GraphCacheMetrics
- Capture
- Cypher support
- .from_args
- .matrix_reachable_with_kernel
- ScopeCloseReservation
- JsonFieldVisitor
- Capture
- s3_bolt_benchmark_server.rs
- query_memory_profile.sh
- QueryCellClient
- semconv.rs
- fence_worker.rs
- deploy_single_node_k3s.sh
- QueryCancellationToken
- GraphBlasCsc
- HydraDB Architecture
- labelSelector
- error_class.rs
- src/lib.rs
- GraphShard
- DurationHistogramSnapshot
- properties
- HydraDB
- run_bolt_protocol
- WriterReopenGate
- TelemetryGuard
- object_store_from_env
- trace_context.rs
- NodeReadiness
- consume_bolt_records
- required
- sole_writer_placement
- Development
- Running it locally
- test_read_transport_json
- bridge.rs
- bolt_config_error
- AGENTS.md
- graphblas_link_search_paths
- HydraDB Helm Chart
- HeartbeatAction
- otlp_export_tests.rs
- ClientTestTlsBundle
- maxOpenScopes
- CLAUDE.md
- main
- Getting Started
- PlacementRefreshHandle
- RefreshState
- run_graph_compute
- Read Consistency
- Writer Ownership And Mutations
- Query Execution
- slatedb-graph-kernel
- ci_local.sh
- ec2_graphblas_benchmark.sh
- remote_scan_options

## God Nodes (most connected - your core abstractions)
1. `validate_component()` - 151 edges
2. `GraphShard` - 149 edges
3. `open_test_shard()` - 137 edges
4. `GraphScope` - 125 edges
5. `QueryContext` - 108 edges
6. `VertexPropertyValue` - 102 edges
7. `QueryBudget` - 99 edges
8. `GraphShard` - 85 edges
9. `QueryResultSet` - 71 edges
10. `EdgeMetadata` - 68 edges

## Surprising Connections (you probably didn't know these)
- `a_successful_promotion_records_the_advisory_cell_writer()` --calls--> `read_cell_writer()`  [INFERRED]
  src/engine/cluster.rs → crates/placement/src/cell_writer.rs
- `the_record_is_not_read_on_the_promote_path()` --calls--> `read_cell_writer()`  [INFERRED]
  src/engine/cluster.rs → crates/placement/src/cell_writer.rs
- `run_node()` --calls--> `validate_node_id()`  [INFERRED]
  src/bin/graph-node.rs → crates/placement/src/heartbeat.rs
- `publish_heartbeat()` --calls--> `put_heartbeat()`  [INFERRED]
  src/bin/graph-node.rs → crates/placement/src/heartbeat.rs
- `withdraw_heartbeat()` --calls--> `delete_heartbeat()`  [INFERRED]
  src/bin/graph-node.rs → crates/placement/src/heartbeat.rs

## Import Cycles
- 2-file cycle: `src/sparse_kernel/graphblas.rs -> src/sparse_kernel/mod.rs -> src/sparse_kernel/graphblas.rs`

## Communities (180 total, 3 thin omitted)

### Community 0 - "Result"
Cohesion: 0.09
Nodes (34): decode_u64(), graph_now_millis(), remote_read_options(), remote_scan_options_for_expected_items(), ReadOptions, EdgeRecord, NeighborBatchEntry, check_optional_query_budget() (+26 more)

### Community 1 - "QueryContext"
Cohesion: 0.04
Nodes (51): CompatibilityQueryClient, main(), Option, Result, BlockingBoltTestClient, BoltTestClient, NativePathBoltTestClient, PagedBoltTestClient (+43 more)

### Community 2 - "graph-indexer.rs"
Cohesion: 0.05
Nodes (76): AsyncMutex, Cow, GraphCluster, advance_scope_cursor(), append_dimensioned(), CachedScopeCluster, completed_scope_sweep(), CycleFailures (+68 more)

### Community 3 - "query/path_procedure.rs"
Cohesion: 0.08
Nodes (78): config_bool(), config_literal_string(), config_number(), config_string(), config_string_list(), config_u64(), ConfigValue, consume_identifier() (+70 more)

### Community 4 - "heartbeat.rs"
Cohesion: 0.06
Nodes (84): a_cell_that_was_never_promoted_reads_as_none(), a_failing_get_is_an_error_and_not_an_absent_record(), a_failing_put_is_reported_and_not_swallowed(), a_later_promotion_overwrites_the_earlier_record(), a_record_round_trips_through_json(), a_written_record_reads_back(), an_invalid_cell_id_fails_before_a_path_is_built(), an_unparseable_record_is_an_error_naming_the_object() (+76 more)

### Community 5 - "query_optimizer.rs"
Cohesion: 0.06
Nodes (54): Attributes, Id, Metadata, RowQueryAccess, RowQueryOptimizerPass, RowQueryPlan, RowQueryPlanGroup, RowQueryPlanPattern (+46 more)

### Community 6 - "query.rs"
Cohesion: 0.07
Nodes (74): QueryColumn, QueryPath, QueryPathNode, QueryResultSet, QueryRow, QueryValue, QueryWindow, Box (+66 more)

### Community 7 - "bolt/tests.rs"
Cohesion: 0.05
Nodes (79): BoltPath, a_write_to_a_non_owner_maps_to_the_not_a_leader_code_with_the_owner_hint(), an_idempotency_conflict_is_visible_and_non_retryable_to_bolt_clients(), authenticated_bolt_connections_use_the_separate_idle_timeout(), bolt_path_conversion_preserves_incoming_relationship_direction(), bolt_pull_uses_snapshot_backed_server_cursor_pages(), bolt_reset_after_run_does_not_start_backend_execution(), bolt_reset_interrupts_active_query_and_returns_connection_to_ready() (+71 more)

### Community 8 - "ObjectStoreWriterLeaseDirectory"
Cohesion: 0.07
Nodes (55): BoltRoutingServer, BoltRoutingTable, ObjectStoreBoltRoutingTableProvider, routing_unavailable(), Arc, BTreeMap, Into, IntoIterator (+47 more)

### Community 9 - "opencypher.rs"
Cohesion: 0.05
Nodes (78): cypher_operator_t, cypher_parse_result_t, aggregate_function_name(), cached_cypher_ast_lowers_each_requests_parameters(), classify_opencypher_query_access(), distinct_order_expression_is_projected(), is_cypher_identifier_continue(), is_cypher_identifier_start() (+70 more)

### Community 10 - "NamespacePath"
Cohesion: 0.06
Nodes (40): DoubleEndedIterator, GraphId, NamespaceId, NamespacePath, Default, Display, Formatter, From (+32 more)

### Community 11 - "http.rs"
Cohesion: 0.07
Nodes (62): HeaderMap, IntoResponse, Json, accepts_ndjson(), authenticate_http(), cancel_query(), ClientHttpServer, enqueue_ndjson() (+54 more)

### Community 12 - "GraphShard"
Cohesion: 0.07
Nodes (29): duration_micros_u64(), Duration, writer_lane_index(), GraphSnapshot, GraphSnapshot<'a>, Arc, GraphShard, Option (+21 more)

### Community 13 - "query_bench.rs"
Cohesion: 0.07
Nodes (67): async_main(), bench_cold_page(), bench_cold_rows(), bench_concurrent_pages(), bench_concurrent_rows(), bench_page_workload(), bench_rows_workload(), BenchEnv (+59 more)

### Community 14 - "FaultStore"
Cohesion: 0.07
Nodes (52): a_failed_list_surfaces_as_a_generic_store_error(), age_of(), backdating_ages_one_object_and_leaves_its_neighbours_alone(), Counters, counters_are_per_operation_and_start_at_zero(), counters_include_the_calls_that_were_failed(), deleting_an_object_forgets_its_backdated_timestamp(), every_metadata_path_reports_the_backdated_timestamp() (+44 more)

### Community 15 - "meter.rs"
Cohesion: 0.07
Nodes (44): a_counter_may_not_claim_a_bucket_bound(), a_duplicate_counter_label_is_rejected(), a_duplicate_label_is_rejected(), a_mismatched_ladder_is_an_error_not_a_panic(), an_unlabelled_counter_is_a_single_series(), attributes_of(), buckets_are_rendered_cumulatively_and_end_at_infinity(), cell_of() (+36 more)

### Community 16 - "String"
Cohesion: 0.07
Nodes (66): hex_encode(), String, adjacency_generation(), cell_drop_idempotency(), cell_drop_marker(), cell_drop_pending_marker(), cell_prefix(), degree_in() (+58 more)

### Community 17 - "validate_component"
Cohesion: 0.15
Nodes (23): ensure_limit(), validate_component(), BulkImportResult, RelationshipImportResult, RelationshipMutation, is_retryable_write_conflict(), coalesce_edge_metadata_updates(), coalesce_relationship_imports() (+15 more)

### Community 18 - "open_test_shard"
Cohesion: 0.03
Nodes (65): batch_neighbor_reads_honor_cancellation_before_storage_scans(), batch_structural_edge_delete_removes_relationships_before_recreate(), bulk_import_edges_writes_normal_indexes_and_idempotency(), bulk_import_transactions_retry_without_epoch_overlap(), concurrent_duplicate_edge_writes_converge_to_one_record(), concurrent_writes_allocate_unique_epochs_through_slate_transactions(), cypher_batches_multi_pattern_create_and_multi_row_delete(), cypher_create_and_match_use_storage_kernel() (+57 more)

### Community 19 - "state.rs"
Cohesion: 0.07
Nodes (41): AsyncRwLock, OwnedMutexGuard, abandon_process_writer_after_runtime_shutdown(), cancelled_caller_cannot_abandon_writer_promotion(), close_reader_after_snapshots(), dropping_after_the_construction_runtime_shuts_down_still_cleans_registration(), dropping_the_final_owner_outside_the_runtime_still_cleans_registration(), final_owner_release_and_reopen_share_one_state_and_gate() (+33 more)

### Community 20 - "properties"
Cohesion: 0.03
Nodes (63): $ref, $ref, $ref, $ref, $ref, $ref, $ref, $ref (+55 more)

### Community 21 - "Self"
Cohesion: 0.07
Nodes (16): KubernetesQueryServiceDiscovery, normalized_sha256_fingerprints(), QueryServiceDiscovery, QueryTransportClientConfig, QueryTransportNamespaceQuotas, QueryTransportScopeAuthorizer, QueryTransportServerConfig, QueryTransportTlsClientConfigProvider (+8 more)

### Community 22 - "graphblas.rs"
Cohesion: 0.12
Nodes (46): GrBDescriptor, GrBIndex, GrBInfo, GrBMatrix, GrBVector, build_compiled_inner(), build_degree_vector(), build_transposed_matrix() (+38 more)

### Community 23 - "codec.rs"
Cohesion: 0.10
Nodes (57): bulk_import_chunk_order(), bulk_import_fingerprint(), commit_txn_strict_with_sequence(), decode_bool_flag(), decode_bulk_import_idempotency(), decode_cell_drop_idempotency(), decode_commit_idempotency(), decode_delete_idempotency() (+49 more)

### Community 24 - "Result"
Cohesion: 0.09
Nodes (28): checked_unique_cell(), column_index(), discovery_node_id(), DistributedQueryCoordinator, DistributedQueryPlanResult, graph_namespace_grant_restricts_descendants_to_one_graph_id(), merge_distributed_inner_join(), merge_distributed_union_all() (+20 more)

### Community 25 - "src/tests.rs"
Cohesion: 0.04
Nodes (18): canonical_graph_records_derive_identity_from_keys(), cypher_float_properties_roundtrip_index_compare_and_order(), cypher_float_properties_roundtrip_index_compare_and_order_inner(), cypher_relationship_properties_are_indexed_mutable_and_snapshot_safe(), cypher_relationship_properties_case(), query_cardinality_stats_refresh_persists_edge_counts(), query_stats_background_refresh_job_publishes_records(), read_query_stats_record_for_test() (+10 more)

### Community 26 - "bolt_benchmark.rs"
Cohesion: 0.10
Nodes (49): ConcurrentTask, assert_read_count(), BenchBoltSession, BenchEnvironment, BenchPaths, BenchRecord, bolt_failure(), collect_concurrent() (+41 more)

### Community 27 - "admin.rs"
Cohesion: 0.09
Nodes (52): accumulate(), accumulate_classes(), admin_io_error(), AdminServer, AdminState, append_counter_types(), append_global_class_counters(), append_global_counters() (+44 more)

### Community 28 - "CompiledGraphBlasMatrix"
Cohesion: 0.13
Nodes (50): CompiledGraphBlasMatrix, AtomicUsize, Mutex, adjacency_kernel_expands_reachable_vertices(), compact_csc_kernel_matches_adjacency_kernel(), compile_graphblas(), compile_graphblas_compact_csc_u32(), compile_graphblas_csc() (+42 more)

### Community 29 - "falkor_import.rs"
Cohesion: 0.12
Nodes (45): ArgParser, component_slug(), decode_jsonl_line(), DuplicatePolicy, EdgeImportState, EdgeImportTotals, EdgeTypeWriteState, flush_edge_type_state() (+37 more)

### Community 30 - "Result"
Cohesion: 0.21
Nodes (52): AstNode, cypher_astnode_type_t, checked_node(), ensure_instance(), function_name(), identifier_name(), integer_u8(), is_count_star() (+44 more)

### Community 31 - "ClientQueryService"
Cohesion: 0.13
Nodes (21): batch_operation_columns(), client_query_key(), client_root_span(), ClientQueryPage, ClientQueryRequest, ClientQueryResult, ClientQueryService, ClientQuerySession (+13 more)

### Community 32 - "Result"
Cohesion: 0.15
Nodes (10): holds_the_writer(), record_error_class(), RoutedGraphCluster, IntoIterator, Item, Result, Vec, VertexId (+2 more)

### Community 33 - "cluster.rs"
Cohesion: 0.18
Nodes (38): a_cold_scope_open_does_not_lock_out_cached_scopes(), a_failing_record_put_does_not_fail_the_promotion(), a_held_loaded_clusters_snapshot_does_not_block_opening_a_new_scope(), a_non_owner_refuses_the_write_and_does_not_promote(), a_parked_metrics_collection_does_not_block_opening_a_new_scope(), a_refused_promotion_records_nothing(), a_shed_view_refuses_with_no_hint_and_does_not_promote(), a_successful_promotion_records_the_advisory_cell_writer() (+30 more)

### Community 34 - "GraphStore"
Cohesion: 0.11
Nodes (16): DbReaderSnapshot, DbSnapshot, Output, GraphStorageSnapshot, GraphStore, Arc, Bytes, Db (+8 more)

### Community 35 - "cache.rs"
Cohesion: 0.10
Nodes (25): BoundedGraphCache, BoundedGraphCache<K, V>, byte_limit_evicts_lru_entries(), CacheEntry, edge_metadata_heap_bytes(), NativePathResultCacheKey, oversized_entry_is_not_retained(), RelationshipPropertyRowsCacheKey (+17 more)

### Community 36 - "engine.rs"
Cohesion: 0.12
Nodes (47): append_matrix_rows_indices(), decode_binary_len(), decode_binary_string(), decode_binary_u32s_from_u64s(), decode_binary_u64(), decode_binary_u64_bytes(), decode_binary_u64s(), decode_graphblas_csc() (+39 more)

### Community 37 - "GraphTopologyOverlay"
Cohesion: 0.09
Nodes (31): collect_wal_topology_entry(), corrupt_wal_topology_entry(), expand_range_with_overlay(), GraphShard, GraphTopologyOverlay, GraphTopologyTail, malformed_wal_topology_isolated_to_its_cell_and_edge_type(), push_wal_topology_edge() (+23 more)

### Community 38 - "VertexPropertyValue"
Cohesion: 0.09
Nodes (31): c_char, Ord, PartialOrd, QueryFloat, Eq, Into, Option, Ordering (+23 more)

### Community 39 - "properties"
Cohesion: 0.04
Nodes (48): type, enum, type, $ref, properties, $ref, $ref, type (+40 more)

### Community 40 - "RecordStore"
Cohesion: 0.08
Nodes (22): ListFailingStore, RecordStore, AtomicBool, AtomicU64, Box, BoxStream, CopyOptions, Debug (+14 more)

### Community 41 - "core/config.rs"
Cohesion: 0.10
Nodes (25): DbReaderOptions, Settings, GraphBackpressurePolicy, GraphCacheConfig, GraphDurabilityConfig, GraphLimits, GraphStorageMemoryConfig, open_graph_db() (+17 more)

### Community 42 - "otel_metrics.rs"
Cohesion: 0.08
Nodes (30): PrometheusHistogram, bounds_render_identically_to_the_meters_rendering(), enumerated_counter_fields(), enumerated_fields(), every_counter_field_reaches_both_exports(), every_histogram_field_reaches_both_exports(), every_shard_counter_is_registered_as_an_instrument(), ExportUnit (+22 more)

### Community 43 - "Option"
Cohesion: 0.13
Nodes (27): RowNodePattern, RowPattern, aggregate_integer_value(), binding_property(), binding_row_bound_names(), binding_row_join_key(), binding_rows_bound_names_union(), BindingRow (+19 more)

### Community 44 - "Into"
Cohesion: 0.09
Nodes (12): Client, ConsulQueryServiceDiscovery, EtcdQueryServiceDiscovery, QueryTransportCancellationPrincipal, QueryTransportPrincipal, QueryTransportScopeGrant, QueryTransportSecret, Debug (+4 more)

### Community 45 - "typed_mutation"
Cohesion: 0.04
Nodes (46): batch_reads_scope_work_to_requested_vertices(), batch_reads_share_one_snapshot_and_preserve_input_order(), committed_edges_stay_readable_after_compaction_then_artifact_gc(), compiled_traversal_reflects_writes_committed_after_the_graph_index_generation(), concurrent_indexers_publish_and_gc_without_regressing_current_generation(), current_epoch_reads_match_acknowledged_history_under_concurrent_reinserts(), current_graph_verifier_detects_relationship_index_corruption(), cypher_cold_graphblas_snapshot_does_not_reacquire_compilation_gate() (+38 more)

### Community 46 - "query_correctness.rs"
Cohesion: 0.13
Nodes (41): CheckResult, assert_exact(), CheckRecord, env_u64(), env_u8(), env_usize(), expected_vertices(), first_page() (+33 more)

### Community 47 - "algebra.rs"
Cohesion: 0.09
Nodes (28): Notify, logical_plan(), LogicalQueryPlan, OriginalBatchOperation, physical_plan(), PhysicalQueryPlan, property_map_resident_bytes(), QueryBatchEdge (+20 more)

### Community 48 - "GraphScope"
Cohesion: 0.15
Nodes (13): GraphMemoryConfig, GraphOpenOptions, GraphScope, process_writer_registry(), GraphCluster, ObjectStoreNodeDirectory, RoutedClusterOpenConfig, Arc (+5 more)

### Community 49 - "Option"
Cohesion: 0.09
Nodes (20): authenticate_query_transport(), constant_time_secret_eq(), crate::ScopedRoutedGraphCluster, DistributedQueryJoin, DistributedQueryLeg, DistributedQueryMerge, DistributedQueryPageRequest, DistributedQueryPlan (+12 more)

### Community 50 - "liveness.rs"
Cohesion: 0.12
Nodes (33): HeartbeatEntry, Duration, a_failed_list_inside_grace_serves_the_cached_live_set(), a_failed_list_never_replaces_the_cached_view(), a_failed_list_past_grace_sheds_and_withdraws_the_heartbeat(), a_heartbeat_exactly_at_the_timeout_is_dead_and_one_tick_younger_is_live(), a_never_published_peer_is_dead_once_the_startup_window_closes(), a_never_published_peer_is_live_inside_the_startup_window() (+25 more)

### Community 51 - "service/tests.rs"
Cohesion: 0.09
Nodes (27): principal_scoped_mutation_idempotency_key(), query_context(), authenticated_session(), caller_mutation_identity_is_stable_within_one_principal(), cursor_service(), dropping_execution_future_cleans_active_query_lifecycle(), expired_server_cursor_releases_its_buffer(), identical_caller_mutation_ids_are_isolated_between_principals() (+19 more)

### Community 52 - "EdgeMetadata"
Cohesion: 0.12
Nodes (22): encode_delete_idempotency(), encode_relationship_delete_idempotency(), relationship_create_fingerprint(), CommitResult, DeleteResult, EdgeMetadata, EdgeMutation, RelationshipCreateResult (+14 more)

### Community 53 - "write.rs"
Cohesion: 0.10
Nodes (33): encode_vertex_property_value_key(), RelationshipRecord, QueryBatchMergePolicy, BTreeSet, accepts_a_newer_patch_without_replacing_create_only_properties(), common_edge_type(), counter_value(), delete_edge_metadata_indexes_txn() (+25 more)

### Community 54 - "GraphCorrectnessReport"
Cohesion: 0.11
Nodes (29): GraphCorrectnessReport, GraphExportDigest, adjacency_from_edges(), checksum_u64(), compare_degree_maps(), compare_edge_sets(), compare_relationship_count_maps(), compare_relationship_property_index_sets() (+21 more)

### Community 55 - "ListFailingStore"
Cohesion: 0.08
Nodes (26): ListFailingStore, PlacementConfig, AtomicBool, Box, BoxStream, CopyOptions, Debug, Default (+18 more)

### Community 56 - "mutation"
Cohesion: 0.05
Nodes (41): adjacency_policy_compiles_no_matrix_at_all(), artifact_build_edge_limit_rejects_loaded_builds(), compact_csc_policy_runs_and_reports_the_compact_kernel(), current_graph_verifier_detects_index_corruption(), current_one_shot_query_uses_slatedb_snapshot(), current_snapshot_preserves_point_edge_across_delete(), current_snapshot_uses_one_slatedb_storage_sequence(), delete_edge_mutations_batch_rejects_duplicate_edge_identities() (+33 more)

### Community 57 - "falkor_query_bench.rs"
Cohesion: 0.16
Nodes (30): BenchRecord, ArgParser, bench_cold_no_cache(), bench_hot_memory(), bench_single_open_query(), bench_warm_disk(), BenchConfig, BenchRecord (+22 more)

### Community 58 - "coordination.rs"
Cohesion: 0.13
Nodes (38): QueryLifecycleToken, acquire_namespace_query_permits(), acquire_query_transport_permit(), activate_query_lifecycle(), authorize_query_transport_scope(), begin_query_lifecycle(), cancel_active_query(), cancel_query_lifecycle_entry() (+30 more)

### Community 59 - "service.rs"
Cohesion: 0.09
Nodes (32): ActiveClientQuery, authentication_error(), client_query_runtime_exceeded(), ClientMutationIdempotencyKey, ClientQueryCredentials, ClientQueryDropGuard, ClientQueryKey, ClientQueryMetrics (+24 more)

### Community 60 - ".format_event"
Cohesion: 0.07
Nodes (28): Capture, fmt_layer(), HydraDBJson, is_reserved_root_key(), RedactingFields, Arc, Box, Event (+20 more)

### Community 61 - "VertexMetadata"
Cohesion: 0.19
Nodes (22): commit_txn_strict(), decode_edge_metadata(), decode_vertex_metadata(), encode_bulk_import_idempotency(), encode_commit_idempotency(), encode_edge_record(), encode_u64(), next_epoch_txn() (+14 more)

### Community 62 - ".from_values"
Cohesion: 0.15
Nodes (32): ConfigResult, graph_node_config_applies_query_scan_edge_limit(), graph_node_config_applies_reader_wal_replay_concurrency(), graph_node_config_can_disable_heavy_memory_caches(), graph_node_config_selects_the_sparse_kernel(), graph_node_rejects_an_excessive_writer_lease_window(), graph_node_rejects_an_unsafe_writer_lease_window(), graph_node_rejects_unsafe_wal_flush_bounds() (+24 more)

### Community 63 - "src/config.rs"
Cohesion: 0.12
Nodes (28): a_nonsense_metric_interval_falls_back(), binaries_do_not_read_each_others_filters(), blank_endpoint_is_treated_as_unset(), env_from(), falls_back_to_info(), headers_split_on_first_equals_only(), logs_export_unless_turned_off(), logs_exporter_none_disables_logs_alone() (+20 more)

### Community 64 - "multigraph_bench.rs"
Cohesion: 0.15
Nodes (27): assert_rows(), bench_generated_create(), bench_read_workload(), env_u32(), main(), multigraph_workloads(), parse_u64_list(), relationship_mutations() (+19 more)

### Community 65 - "GraphError"
Cohesion: 0.09
Nodes (25): GraphError, Duration, Error, Option, Self, StorageSequence, ActiveQueryTransportConnection, query_transport_client_timeout() (+17 more)

### Community 66 - "GraphWriteBatch"
Cohesion: 0.13
Nodes (26): E, GraphWriteOp, LocalWriteGuard, GraphWriteBatch, GraphWriteGuard, Bytes, K, Self (+18 more)

### Community 67 - "corpus.rs"
Cohesion: 0.14
Nodes (24): json_escape(), main(), collect_feature_files(), CypherTckCase, CypherTckCompatibilityReport, CypherTckCorpus, looks_like_vertex_id_column(), parse_expected_list() (+16 more)

### Community 68 - "VertexId"
Cohesion: 0.18
Nodes (6): Range, CompactOrdinalVec, CompiledCompactCscMatrix, BTreeSet, Vec, VertexId

### Community 69 - "GraphIndexGeneration"
Cohesion: 0.19
Nodes (22): graphblas_csc_checksum(), decode_graph_index_csc(), decode_graph_index_manifest(), decode_index_u64(), decode_index_u64s(), encode_graph_index_csc(), encode_graph_index_manifest(), encode_index_u64s() (+14 more)

### Community 70 - "NodeHistograms"
Cohesion: 0.12
Nodes (20): CounterError, HistogramError, collect_forever(), collect_once(), CounterQuantity, MetricCollection, NodeCounters, NodeHistograms (+12 more)

### Community 71 - "Result"
Cohesion: 0.15
Nodes (16): FromStr, canonical_database_component(), ClientBookmark, ClientQueryTarget, encode_database_scope_id(), hex_decode(), hex_nibble(), HierarchicalClientDatabaseResolver (+8 more)

### Community 72 - "PlacementView"
Cohesion: 0.12
Nodes (17): LiveView, CellOwnership, lock(), only_a_remote_owner_produces_a_hint(), PlacementView, read_lock(), Arc, Mutex (+9 more)

### Community 73 - "propagate.rs"
Cohesion: 0.09
Nodes (14): decode_hex(), hex_value(), parse_hex_byte(), preserves_unknown_flag_bits(), round_trips_the_spec_example(), Display, Error, Formatter (+6 more)

### Community 74 - "Result"
Cohesion: 0.21
Nodes (28): allowlisted_caller_value(), bolt_bookmarks_from_extra(), bolt_client_credentials(), bolt_mutation_idempotency_key(), bolt_query_request(), bolt_read_consistency(), bolt_route_span(), bolt_routing_table() (+20 more)

### Community 75 - "otlp.rs"
Cohesion: 0.11
Nodes (25): an_endpoint_builds_all_three_pipelines(), build(), build_resource(), denylisted_span_attributes_never_reach_the_exporter(), logs_off_drops_the_appender_but_keeps_traces_and_metrics(), no_endpoint_builds_nothing(), Providers, RedactingSpanProcessor (+17 more)

### Community 76 - "meter_export.rs"
Cohesion: 0.10
Nodes (25): a_counter_reaches_the_exporter_as_a_monotonic_sum_per_cell(), a_metric_recorded_through_the_guards_meter_reaches_an_otlp_exporter(), an_unrecorded_counter_exports_nothing(), an_unrecorded_histogram_exports_nothing(), attributes_of(), Capture, contains(), lookup() (+17 more)

### Community 77 - "BoltServerConfig"
Cohesion: 0.14
Nodes (12): BoltServerConfig, BoltRoutingTableProvider, Send, Sync, Arc, Duration, Into, Self (+4 more)

### Community 78 - "Self"
Cohesion: 0.11
Nodes (8): ClientQueryServiceConfig, ClientReadConsistency, AsRef, Default, IntoIterator, Item, Self, sanitize_caller_metadata()

### Community 79 - "enabled"
Cohesion: 0.07
Nodes (29): items, type, uniqueItems, properties, type, type, additionalDnsNames, certManager (+21 more)

### Community 80 - "FailingStore"
Cohesion: 0.12
Nodes (20): FailingStore, Box, BoxStream, CopyOptions, Display, Error, Formatter, GetOptions (+12 more)

### Community 81 - ".new"
Cohesion: 0.09
Nodes (18): bolt_io_error(), BoltMessageWriter<W>, BoltReaderTask, BoltServerHandle, BoltServerMetrics, ClientBoltServer, request(), reused_process_local_query_ids_get_distinct_durable_mutation_ids() (+10 more)

### Community 82 - "TcpQueryCellClient"
Cohesion: 0.16
Nodes (6): PooledQueryTransportConnection, Box, Instant, TcpQueryCellClient, transport_protocol_error(), transport_remote_error()

### Community 83 - "enum"
Cohesion: 0.08
Nodes (28): properties, required, type, type, $ref, type, cache, emptyDir (+20 more)

### Community 84 - ".should_sample"
Cohesion: 0.13
Nodes (21): a_data_attribute_never_forces_a_keep(), a_false_flag_does_not_force_a_keep(), explicit_force_attribute_is_honoured(), HydraDBSampler, ratio_decision_is_deterministic_in_the_trace_id(), ratio_one_keeps_everything(), ratio_selects_roughly_the_requested_share(), ratio_zero_still_keeps_writer_spans() (+13 more)

### Community 85 - "placement.rs"
Cohesion: 0.28
Nodes (20): a_clone_sees_the_refresh_its_sibling_performed(), a_known_empty_fleet_promotes_where_a_shed_view_refuses(), a_list_failure_inside_grace_still_serves_the_cached_view(), a_list_failure_past_grace_sheds_and_refuses_with_no_hint(), a_lone_node_owns_its_cell(), a_node_absent_from_the_heartbeats_is_not_a_candidate(), a_node_whose_list_never_works_sheds_one_timeout_after_start(), a_recovered_list_restores_the_view_after_shedding() (+12 more)

### Community 86 - "graph-node.rs"
Cohesion: 0.21
Nodes (26): boot(), heartbeat_tracks_readiness_in_both_directions(), install_trace_context_bridge(), main(), publish_heartbeat(), ready_node(), Arc, DateTime (+18 more)

### Community 87 - ".build_matrix_tiles"
Cohesion: 0.19
Nodes (18): GraphShard, prepare_matrix_artifact_build(), publish_matrix_artifact_manifests(), publish_matrix_artifact_manifests_with_cell_lock(), BTreeMap, Instant, MatrixAdjacency, Option (+10 more)

### Community 88 - "required"
Cohesion: 0.08
Nodes (26): definitions, indexerWorkload, positiveUnsignedDecimal, unsignedDecimal, workload, $comment, required, type (+18 more)

### Community 89 - "head_sampling.rs"
Cohesion: 0.12
Nodes (18): a_data_attribute_at_span_creation_does_not_keep_the_trace(), a_force_recorded_after_the_span_starts_cannot_keep_the_trace(), a_force_set_at_span_creation_keeps_the_trace(), a_forced_child_cannot_resurrect_a_dropped_root(), Capture, exported_spans(), Arc, Context (+10 more)

### Community 90 - ".compact_out_adjacency_segments_locked"
Cohesion: 0.18
Nodes (11): GraphShard, Bytes, DbIterator, Instant, Option, Result, StorageSequence, Vec (+3 more)

### Community 91 - ".deny"
Cohesion: 0.17
Nodes (8): is_redacted(), RedactingVisitor, RedactingVisitor<'a>, Debug, Error, Field, Self, Visit

### Community 92 - "properties"
Cohesion: 0.08
Nodes (24): items, maxItems, minItems, type, uniqueItems, minLength, type, minLength (+16 more)

### Community 93 - "layers.rs"
Cohesion: 0.16
Nodes (23): a_field_colliding_with_a_reserved_root_key_stays_nested(), a_field_used_as_the_message_fallback_is_not_also_flattened(), a_line_outside_any_request_carries_no_tenancy(), a_message_only_event_has_no_fields_object(), a_tenant_without_a_sub_tenant_still_promotes(), an_event_field_outranks_the_same_field_on_the_span(), capture_json(), error_text_never_becomes_the_error_type() (+15 more)

### Community 94 - "properties"
Cohesion: 0.09
Nodes (23): type, properties, required, type, minLength, type, minLength, type (+15 more)

### Community 95 - "properties"
Cohesion: 0.09
Nodes (23): properties, type, type, type, properties, type, type, auth (+15 more)

### Community 96 - "locality.rs"
Cohesion: 0.13
Nodes (17): PrefixExtractor, PrefixTarget, compare_locality_layouts(), locality_cell_id(), locality_cell_prefix(), locality_cell_prefix_len(), LocalityCellExtractor, LocalityLayoutExperiment (+9 more)

### Community 97 - "Arc"
Cohesion: 0.19
Nodes (9): RustlsClientConfig, RustlsServerConfig, ReloadableQueryTransportTlsClientConfigProvider, ReloadableQueryTransportTlsServerConfigProvider, Arc, AtomicU64, RwLock, StaticQueryTransportTlsClientConfigProvider (+1 more)

### Community 98 - "Option"
Cohesion: 0.15
Nodes (21): and_row_predicates(), collect_match_clause_bindings(), collect_row_node_bindings(), collect_row_pattern_bindings(), edge_metadata_from_edge_pattern(), lower_create_mutations(), lower_simple_merge(), lowers_mutation_queries() (+13 more)

### Community 99 - ".try_execute_graph_kernel_opencypher_rows_page"
Cohesion: 0.17
Nodes (7): graph_kernel_node_id_rows(), graph_kernel_order_vertices(), graph_kernel_window_sorted_vertices(), query_next_cursor(), ReachableWindowRequest, Instant, validate_query_result_window()

### Community 100 - "tls.rs"
Cohesion: 0.16
Nodes (18): CertificateDer, DefaultHasher, PrivateKeyDer, file_tls_reloader_rotates_after_atomic_secret_update(), FileTlsReloader, load_certificate_material(), load_server_config(), Arc (+10 more)

### Community 101 - "networkPolicyPeer"
Cohesion: 0.09
Nodes (22): minLength, type, networkPolicyPeer, items, type, additionalProperties, properties, required (+14 more)

### Community 102 - "properties"
Cohesion: 0.09
Nodes (22): type, required, type, $ref, $ref, required, type, properties (+14 more)

### Community 103 - "runtime_smoke.sh"
Cohesion: 0.09
Nodes (20): CLOUD_PROVIDER, GRAPH_ADMIN_ADDR, GRAPH_ADVERTISED_BOLT_ADDR, GRAPH_ALLOW_PLAINTEXT, GRAPH_AUTH_TOKEN_FILE, GRAPH_BOLT_ADDR, GRAPH_BOLT_NODE_ADDRESSES, GRAPH_CELL_ID (+12 more)

### Community 104 - "bolt.rs"
Cohesion: 0.21
Nodes (20): a_malformed_dict_is_still_a_protocol_error(), a_traceparent_is_read_from_its_own_reader(), allowlisted_keys_are_read(), bolt_caller_metadata(), BoltCallerMetadata, BoltState, caller_mutation_id_is_stable_across_bolt_retries(), correlation_keys_do_not_disturb_consistency() (+12 more)

### Community 105 - "model.rs"
Cohesion: 0.15
Nodes (17): encode_cell_drop_idempotency(), BulkImportDuplicatePolicy, BulkImportOptions, EdgeDeleteBatchResult, EdgeExistenceBatchEntry, EdgeIngestOptions, EdgeIngestResult, EdgeMutationBatchResult (+9 more)

### Community 106 - "corrupt"
Cohesion: 0.25
Nodes (15): adjacency_edge_count(), adjacency_resident_bytes(), corrupt(), decode_graphblas_csc_manifest(), graphblas_csc_key(), GraphShard, Arc, MatrixAdjacency (+7 more)

### Community 107 - "properties"
Cohesion: 0.10
Nodes (21): pattern, type, properties, required, type, digest, image, pullPolicy (+13 more)

### Community 108 - "http/tests.rs"
Cohesion: 0.16
Nodes (13): http_api_enforces_auth_scope_and_returns_typed_json(), http_api_serves_authenticated_queries_over_https(), http_scope(), http_service(), http_strong_consistency_refreshes_the_slatedb_reader(), HttpTestClient, ndjson_stream_uses_one_snapshot_backed_server_cursor(), Arc (+5 more)

### Community 109 - "ScopedRoutedGraphCluster"
Cohesion: 0.11
Nodes (20): GraphShard, Result, StorageSequence, ArtifactGcResult, edge_set(), graph_artifact_epoch_from_key(), graph_artifact_gc_prefixes(), ObjectStoreNodeDirectory (+12 more)

### Community 110 - "properties"
Cohesion: 0.11
Nodes (20): maximum, minimum, type, type, type, $ref, service, $ref (+12 more)

### Community 111 - "GraphCacheMetrics"
Cohesion: 0.16
Nodes (10): GraphCacheKind, GraphCacheMetrics, GraphOperationalMetrics, GraphOperationalMetricsSnapshot, load_class_counters(), AtomicU64, ErrorClassCounters, GraphCacheEntryCounts (+2 more)

### Community 112 - "Capture"
Cohesion: 0.18
Nodes (10): Capture, RedactingSpanProcessor<P>, Arc, Context, Duration, Mutex, OTelSdkResult, Span (+2 more)

### Community 113 - "Cypher support"
Cohesion: 0.11
Nodes (18): Batches with UNWIND, Checking a query without running it, CREATE, Cypher support, MERGE, Not supported, Path procedures, Patterns (+10 more)

### Community 114 - ".from_args"
Cohesion: 0.23
Nodes (12): ArgParser, format_float(), format_property_value(), format_query_value(), main(), print_result(), print_usage(), QueryConfig (+4 more)

### Community 115 - ".matrix_reachable_with_kernel"
Cohesion: 0.20
Nodes (12): GraphCachePolicy, Default, Option, Self, BenchmarkResult, MatrixTraversalResult, GraphShard, Result (+4 more)

### Community 116 - "ScopeCloseReservation"
Cohesion: 0.13
Nodes (12): close_routed_shards_best_effort(), close_shards_best_effort(), AtomicUsize, BTreeMap, Drop, GraphShard, Mutex, Receiver (+4 more)

### Community 117 - "JsonFieldVisitor"
Cohesion: 0.25
Nodes (7): JsonFieldVisitor, Debug, Error, Field, Value, Visit, Map

### Community 118 - "Capture"
Cohesion: 0.14
Nodes (14): an_event_inside_a_span_carries_hex_trace_and_span_ids(), Capture, capture_with_tracer(), ids_group_events_by_span_not_by_line(), Arc, FnOnce, MakeWriter, Mutex (+6 more)

### Community 119 - "s3_bolt_benchmark_server.rs"
Cohesion: 0.21
Nodes (17): env_bool(), env_u64(), graph_options(), layered_edges(), main(), proc_status_kib(), process_memory_kib(), required_env() (+9 more)

### Community 120 - "query_memory_profile.sh"
Cohesion: 0.11
Nodes (17): GRAPH_COMPILED_KERNEL, GRAPH_QUERY_BENCH_BULK_CHUNK_SIZE, GRAPH_QUERY_BENCH_COLD_ITERS, GRAPH_QUERY_BENCH_CONCURRENT_ITERS, GRAPH_QUERY_BENCH_DATA_HOPS, GRAPH_QUERY_BENCH_DISK_CACHE_BYTES, GRAPH_QUERY_BENCH_HOPS, GRAPH_QUERY_BENCH_HOT_ITERS (+9 more)

### Community 121 - "QueryCellClient"
Cohesion: 0.21
Nodes (6): QueryCellClient, JoinHandle, Mutex, Sender, SocketAddr, TcpQueryServer

### Community 122 - "semconv.rs"
Cohesion: 0.14
Nodes (7): every_metric_label_is_a_registry_key(), every_registry_key_is_classified_exactly_once(), metric_labels_are_unique(), MetricLabel, Display, Formatter, Result

### Community 123 - "fence_worker.rs"
Cohesion: 0.35
Nodes (16): env_u64(), graph_options(), incumbent(), io_error(), load_object_store(), main(), mutation(), reader() (+8 more)

### Community 124 - "deploy_single_node_k3s.sh"
Cohesion: 0.24
Nodes (14): apply_secret_tls(), certificate_matches_host(), die(), is_ipv4(), log(), need_command(), privileged(), secret_exists() (+6 more)

### Community 125 - "QueryCancellationToken"
Cohesion: 0.17
Nodes (8): client_query_cancelled(), F, OwnedSemaphorePermit, T, QueryCancellationToken, AtomicBool, Eq, PartialEq

### Community 126 - "GraphBlasCsc"
Cohesion: 0.32
Nodes (9): compact_csc_query_bytes(), compact_csc_resident_bytes(), compact_empty_traversal(), compiled_kernel(), graphblas_replica_count(), native_graphblas_resident_bytes(), Self, validate_csc() (+1 more)

### Community 127 - "HydraDB Architecture"
Cohesion: 0.13
Nodes (15): Authority Boundaries, Bolt Routing And Failover, Cache Hierarchy, Client Boundary, Code Map, Coordination And Index Objects, Core Invariants, Failure Semantics (+7 more)

### Community 128 - "labelSelector"
Cohesion: 0.13
Nodes (15): type, labelSelector, minProperties, additionalProperties, anyOf, properties, type, items (+7 more)

### Community 129 - "error_class.rs"
Cohesion: 0.21
Nodes (8): class_strings_are_lower_snake(), class_strings_are_unique(), ErrorClass, only_contention_fencing_and_routing_are_expected(), Outcome, Display, Formatter, Result

### Community 130 - "src/lib.rs"
Cohesion: 0.25
Nodes (13): Namespace, concurrent_reads(), cypher_identifier(), execute_read(), latency_record(), main(), nearest_rank(), parse_args() (+5 more)

### Community 131 - "GraphShard"
Cohesion: 0.15
Nodes (13): NativePathResultCacheValue, GraphShard, GraphWriteAuthority, HashSet, MatrixAdjacency, Semaphore, Vec, VertexId (+5 more)

### Community 132 - "DurationHistogramSnapshot"
Cohesion: 0.19
Nodes (7): AtomicDurationHistogram, DurationHistogramSnapshot, AtomicU64, Duration, Item, Iterator, Option

### Community 133 - "properties"
Cohesion: 0.15
Nodes (14): type, items, type, items, type, $ref, $ref, properties (+6 more)

### Community 134 - "HydraDB"
Cohesion: 0.14
Nodes (14): Architecture, Benchmarks, Contributing, Development, Documentation, HydraDB, Kubernetes, License (+6 more)

### Community 135 - "run_bolt_protocol"
Cohesion: 0.21
Nodes (14): bolt_result_summary_metadata(), bolt_tls_identity(), PendingBoltResult, Box, Instant, OwnedSemaphorePermit, S, SocketAddr (+6 more)

### Community 136 - "WriterReopenGate"
Cohesion: 0.32
Nodes (9): a_fence_waits_one_heartbeat_interval_and_resets_the_ladder_to_its_floor(), fencing_repeatedly_never_advances_the_ladder(), origin(), releasing_a_non_final_process_owner_never_hides_the_writer(), Duration, Instant, success_clears_the_wait_and_the_ladder_together(), the_failure_ladder_doubles_before_each_wait_and_stops_at_the_maximum() (+1 more)

### Community 137 - "TelemetryGuard"
Cohesion: 0.22
Nodes (10): install(), init(), Debug, Drop, Formatter, Option, Result, TelemetryError (+2 more)

### Community 138 - "object_store_from_env"
Cohesion: 0.17
Nodes (12): main(), Result, selected_matrix_kernel(), local_object_store(), object_store_from_env(), AsRef, ObjectStore, Path (+4 more)

### Community 139 - "trace_context.rs"
Cohesion: 0.19
Nodes (11): OnceLock, adopt_remote_parent(), current_traceparent(), install_trace_context_bridge(), malformed_values_are_dropped_rather_than_raised(), Option, Result, Send (+3 more)

### Community 140 - "NodeReadiness"
Cohesion: 0.27
Nodes (7): a_node_is_unready_until_its_listeners_are_up(), a_shed_placement_view_withdraws_the_heartbeat_of_a_healthy_node(), NodeReadiness, readiness(), Arc, AtomicBool, Self

### Community 141 - "consume_bolt_records"
Cohesion: 0.29
Nodes (13): await_bolt_page(), BoltConnectionChannels, BoltMessageWriter, BoltRecordDisposition, consume_bolt_records(), PageAwaitResult, ChunkWriter, ClientMessage (+5 more)

### Community 143 - "required"
Cohesion: 0.17
Nodes (11): required, $schema, type, auth, graph, image, indexer, node (+3 more)

### Community 144 - "sole_writer_placement"
Cohesion: 0.31
Nodes (11): fast_fence_options(), placement_over(), reader_built_generation_tail_covers_commits_in_its_own_wal_file(), routed_cluster_lease_prevents_cross_node_writer_fencing(), routed_cluster_readers_open_every_configured_cell(), routed_reader_catches_up_to_a_remote_writer_storage_sequence(), scoped_routed_cluster_isolates_collection_writers_and_registers_scopes(), scoped_routed_cluster_returns_empty_rows_without_registering_an_unwritten_scope() (+3 more)

### Community 145 - "Development"
Cohesion: 0.22
Nodes (5): Development, Docker And MinIO Harnesses, Local Harnesses, Standalone Scripts, Verification Recipes

### Community 148 - "Running it locally"
Cohesion: 0.22
Nodes (9): 1. Native dependencies, 2. Verify the native libraries, 3. Write the environment file, 4. Smoke-test the storage kernel, 5. Python driver for the Bolt checks, 6. Full runtime smoke, 7. Start a node you can connect to, 8. Prove it works (+1 more)

### Community 149 - "test_read_transport_json"
Cohesion: 0.36
Nodes (9): BufReader, TcpStream, Value, tcp_query_transport_guarded_batch_uses_a_distinct_wire_operation(), tcp_query_transport_never_replays_after_execution_loses_response(), tcp_query_transport_server_rejects_obsolete_client_version(), test_read_transport_json(), test_transport_rows_response() (+1 more)

### Community 150 - "bridge.rs"
Cohesion: 0.31
Nodes (7): a_malformed_traceparent_is_ignored(), a_well_formed_traceparent_is_adopted(), adopt_remote_parent(), current_trace_ids(), current_traceparent(), Option, Span

### Community 151 - "bolt_config_error"
Cohesion: 0.25
Nodes (7): bolt_config_error(), BoltIo, AsyncRead, AsyncWrite, Send, Unpin, T

### Community 152 - "AGENTS.md"
Cohesion: 0.29
Nodes (6): Build and test through the justfile, Failure modes worth knowing before you debug, Layout, Repository conventions, Things that will mislead you, What this repository is

### Community 153 - "graphblas_link_search_paths"
Cohesion: 0.52
Nodes (6): command_stdout(), graphblas_link_search_paths(), main(), pkg_config_link_dirs(), Option, Vec

### Community 154 - "HydraDB Helm Chart"
Cohesion: 0.29
Nodes (7): Cache Storage, HydraDB Helm Chart, Image Publication, Install, Requirements, Security, Upgrades

### Community 156 - "otlp_export_tests.rs"
Cohesion: 0.43
Nodes (6): contains(), CapturedRequests, Vec, shards(), spawn_collector(), the_shard_counters_reach_an_otlp_collector_summed_by_cell()

### Community 157 - "ClientTestTlsBundle"
Cohesion: 0.33
Nodes (6): client_test_tls_bundle(), ClientTestTlsBundle, Arc, ClientConfig, ServerConfig, Vec

### Community 158 - "maxOpenScopes"
Cohesion: 0.40
Nodes (5): maximum, minimum, $ref, type, maxOpenScopes

### Community 159 - "CLAUDE.md"
Cohesion: 0.40
Nodes (3): Build and test through the justfile, Never create artifacts, Plan documents

### Community 160 - "main"
Cohesion: 0.40
Nodes (4): main(), Box, Error, Result

### Community 161 - "Getting Started"
Cohesion: 0.40
Nodes (5): Clone and verify, Getting Started, Prerequisites, Run a local server, Verify a running node

### Community 162 - "PlacementRefreshHandle"
Cohesion: 0.50
Nodes (3): PlacementRefreshHandle, Drop, JoinHandle

### Community 163 - "RefreshState"
Cohesion: 0.70
Nodes (3): RefreshState, Duration, Instant

### Community 164 - "run_graph_compute"
Cohesion: 0.60
Nodes (5): Arc, F, T, run_graph_compute(), run_graph_compute_inline()

### Community 165 - "Read Consistency"
Cohesion: 0.50
Nodes (4): Causal, Indexed Base Plus WAL Overlay, Read Consistency, Strong

### Community 166 - "Writer Ownership And Mutations"
Cohesion: 0.50
Nodes (4): Durable Writer Lease, Liveness And Placement, Mutation Commit, Writer Ownership And Mutations

### Community 167 - "Query Execution"
Cohesion: 0.67
Nodes (3): Common Pipeline, Native Path Procedures, Query Execution

### Community 168 - "slatedb-graph-kernel"
Cohesion: 0.67
Nodes (3): hydradb-placement, hydradb-telemetry, slatedb-graph-kernel

### Community 171 - "remote_scan_options"
Cohesion: 0.67
Nodes (3): remote_prefix_scans_do_not_pollute_the_block_cache(), remote_scan_options(), ScanOptions

## Knowledge Gaps
- **341 isolated node(s):** `$schema`, `type`, `type`, `repository`, `pullPolicy` (+336 more)
  These have ≤1 connection - possible missing edges or undocumented components.
- **3 thin communities (<3 nodes) omitted from report** — run `graphify query` to explore isolated nodes.

## Suggested Questions
_Questions this graph is uniquely positioned to answer:_

- **Why does `String` connect `String` to `Result`, `QueryContext`, `graph-indexer.rs`, `query/path_procedure.rs`, `heartbeat.rs`, `query_optimizer.rs`, `query.rs`, `bolt/tests.rs`, `ObjectStoreWriterLeaseDirectory`, `opencypher.rs`, `NamespacePath`, `http.rs`, `GraphShard`, `query_bench.rs`, `meter.rs`, `validate_component`, `state.rs`, `Self`, `codec.rs`, `Result`, `src/tests.rs`, `bolt_benchmark.rs`, `admin.rs`, `falkor_import.rs`, `Result`, `ClientQueryService`, `Result`, `cluster.rs`, `GraphStore`, `cache.rs`, `engine.rs`, `GraphTopologyOverlay`, `VertexPropertyValue`, `otel_metrics.rs`, `Option`, `Into`, `algebra.rs`, `GraphScope`, `Option`, `liveness.rs`, `service/tests.rs`, `EdgeMetadata`, `write.rs`, `GraphCorrectnessReport`, `ListFailingStore`, `falkor_query_bench.rs`, `coordination.rs`, `service.rs`, `.format_event`, `VertexMetadata`, `.from_values`, `src/config.rs`, `multigraph_bench.rs`, `GraphError`, `GraphWriteBatch`, `corpus.rs`, `GraphIndexGeneration`, `Result`, `PlacementView`, `Result`, `meter_export.rs`, `BoltServerConfig`, `Self`, `TcpQueryCellClient`, `graph-node.rs`, `.build_matrix_tiles`, `head_sampling.rs`, `locality.rs`, `Arc`, `Option`, `bolt.rs`, `model.rs`, `corrupt`, `ScopedRoutedGraphCluster`, `GraphCacheMetrics`, `.from_args`, `ScopeCloseReservation`, `JsonFieldVisitor`, `s3_bolt_benchmark_server.rs`, `QueryCellClient`, `GraphShard`, `run_bolt_protocol`, `TelemetryGuard`, `object_store_from_env`, `trace_context.rs`, `bridge.rs`, `graphblas_link_search_paths`, `otlp_export_tests.rs`?**
  _High betweenness centrality (0.534) - this node is a cross-community bridge._
- **Why does `TestMtlsBundle` connect `src/tests.rs` to `String`, `EdgeMetadata`?**
  _High betweenness centrality (0.038) - this node is a cross-community bridge._
- **Why does `GraphShard` connect `GraphShard` to `GraphStore`, `cache.rs`, `GraphIndexGeneration`, `query.rs`, `GraphTopologyOverlay`, `core/config.rs`, `query_bench.rs`, `GraphCacheMetrics`, `String`, `state.rs`, `.matrix_reachable_with_kernel`, `.build_matrix_tiles`, `CompiledGraphBlasMatrix`?**
  _High betweenness centrality (0.032) - this node is a cross-community bridge._
- **Are the 141 inferred relationships involving `validate_component()` (e.g. with `.new()` and `.cancel()`) actually correct?**
  _`validate_component()` has 141 INFERRED edges - model-reasoned connections that need verification._
- **What connects `$schema`, `type`, `type` to the rest of the system?**
  _341 weakly-connected nodes found - possible documentation gaps or missing edges._
- **Should `Result` be split into smaller, more focused modules?**
  _Cohesion score 0.08571428571428572 - nodes in this community are weakly interconnected._
- **Should `QueryContext` be split into smaller, more focused modules?**
  _Cohesion score 0.03896774193548387 - nodes in this community are weakly interconnected._