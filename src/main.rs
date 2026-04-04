use std::env;
use std::process;

fn main() {
    // Initialize structured logging with NEXUS6_LOG env var support.
    // Usage: NEXUS6_LOG=debug nexus6 loop
    // Default level: info
    let filter = tracing_subscriber::EnvFilter::try_from_env("NEXUS6_LOG")
        .unwrap_or_else(|_| tracing_subscriber::EnvFilter::new("info"));

    tracing_subscriber::fmt()
        .with_env_filter(filter)
        .with_target(false)
        .with_timer(tracing_subscriber::fmt::time::uptime())
        .init();

    let args: Vec<String> = env::args().collect();

    match nexus6::cli::parser::parse_args(&args) {
        Ok(cmd) => {
            if let Err(e) = nexus6::cli::runner::run(cmd) {
                tracing::error!("{}", e);
                process::exit(1);
            }
        }
        Err(e) => {
            tracing::error!("{}", e);
            nexus6::cli::runner::run(nexus6::cli::parser::CliCommand::Help).ok();
            process::exit(1);
        }
    }
}
