"""
=================================================================
  EV Infrastructure Optimization — Main Runner
  
  This is the ENTRY POINT for the entire project.
  It runs all 4 phases sequentially.
  
  Usage:
    python main.py              # Run all phases
    python main.py --phase 1    # Run only Phase 1
    python main.py --phase 2    # Run only Phase 2
    python main.py --download   # Download datasets first
=================================================================
"""

import os
import sys
import argparse
from datetime import datetime


def main():
    parser = argparse.ArgumentParser(
        description="EV Infrastructure Optimization — India",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --download     Download datasets from Kaggle
  python main.py --process      Process raw data only
  python main.py --phase 1      Run demand forecasting
  python main.py --phase 2      Run geospatial clustering
  python main.py --phase 3      Run grid optimization
  python main.py --phase 4      Run financial analysis
  python main.py                Run all phases
        """,
    )
    parser.add_argument("--download", action="store_true", help="Download datasets from Kaggle")
    parser.add_argument("--process", action="store_true", help="Run data processing pipeline")
    parser.add_argument("--phase", type=int, choices=[1, 2, 3, 4], help="Run specific phase")
    parser.add_argument("--all", action="store_true", help="Run all phases sequentially")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("  🚗⚡ EV INFRASTRUCTURE OPTIMIZATION — INDIA")
    print(f"  Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    # ── Download ──
    if args.download:
        from download_datasets import download_all, check_dependencies
        check_dependencies()
        download_all()
        return
    
    # ── Process ──
    if args.process or args.all or args.phase:
        print("\n📦 STEP 0: Data Processing Pipeline")
        print("─" * 40)
        try:
            from src.data.processing import run_pipeline
            run_pipeline()
        except FileNotFoundError as e:
            print(f"  ❌ {e}")
            print("  → Run: python main.py --download")
            return
    
    # ── Phase 1: Forecasting ──
    if args.phase == 1 or args.all or (not args.phase and not args.download and not args.process):
        print("\n\n🔮 PHASE 1: Demand Forecasting")
        print("─" * 40)
        try:
            from src.models.forecasting import run_forecasting_pipeline
            run_forecasting_pipeline()
        except Exception as e:
            print(f"  ❌ Phase 1 error: {e}")
    
    # ── Phase 2: Clustering ──
    if args.phase == 2 or args.all:
        print("\n\n🗺️  PHASE 2: Geospatial Optimization")
        print("─" * 40)
        try:
            from src.models.clustering import run_clustering_pipeline
            run_clustering_pipeline()
        except Exception as e:
            print(f"  ❌ Phase 2 error: {e}")
    
    # ── Phase 3: Optimization ──
    if args.phase == 3 or args.all:
        print("\n\n⚡ PHASE 3: Grid Load Optimization")
        print("─" * 40)
        try:
            from src.models.optimization import run_optimization_pipeline
            run_optimization_pipeline()
        except Exception as e:
            print(f"  ❌ Phase 3 error: {e}")
    
    # ── Phase 4: Financial ──
    if args.phase == 4 or args.all:
        print("\n\n💰 PHASE 4: Financial & Policy Modeling")
        print("─" * 40)
        try:
            from src.models.financial import run_financial_analysis
            run_financial_analysis()
        except Exception as e:
            print(f"  ❌ Phase 4 error: {e}")
    
    print("\n" + "=" * 60)
    print("  ✅ ALL DONE!")
    print("  Results saved in: results/")
    print("=" * 60)


if __name__ == "__main__":
    main()
