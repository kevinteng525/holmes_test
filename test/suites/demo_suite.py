metadata = dict(
    name='demo_suite',
    domain='codegen'
)

case_root = 'test/cases/demo'

selector = dict(
    include_labels=['demo'],
    exclude_labels=['flaky']
)

environment = dict(
    type='vm+docker',
    dependencies=dict(
        pypi_packages=[
            "demo==67.6.1",
        ],
    )
)

runtime = dict(
    resources=dict(
        cpu=9,
    ),
    labels='OAM-810'
)

env_file = "environments/suite_level/demo.env"