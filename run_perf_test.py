import json
from analytics.performance_tracker import performance_tracker

if __name__ == '__main__':
    try:
        stats = performance_tracker.get_global_stats(30)
        print(json.dumps(stats, ensure_ascii=False, indent=2))
    except Exception as e:
        import traceback
        print('EXCEPTION:', e)
        traceback.print_exc()
