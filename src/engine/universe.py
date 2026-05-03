import logging
from typing import List, Dict, Tuple
from src.config import Config

logger = logging.getLogger("UniverseFilter")

class UniverseFilter:
    """
    Filters the merged market snapshot into a tradable universe.
    Applies Market Cap, Volume (Turnover), and Open Interest filters.
    """

    def filter_assets(self, snapshot: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        Filters assets based on configured thresholds.
        Returns (included_assets, excluded_assets).
        Excluded assets include the reason for exclusion.
        """
        included = []
        excluded = []

        for asset in snapshot:
            symbol = asset["symbol"]
            mkt_cap = asset.get("market_cap")
            # We use turnover_24h as the primary volume metric in USDT
            turnover_24h = asset.get("turnover_24h", 0)
            oi_value = asset.get("open_interest_value", 0)
            
            # Overextension is not a hard exclusion by default in this phase.
            # However, if the flag is enabled, we check for it.
            # At this phase, overextension status might not be present in the snapshot yet,
            # but we implement the logic for future compatibility as requested.
            is_overextended = asset.get("is_overextended", False)

            reasons = []

            # Market Cap Filter (if data available)
            # Some new coins might not have market cap data on CG yet; 
            # we can decide whether to exclude or include them. 
            # Usually, if we have a strict MIN_MARKET_CAP, we exclude unknown.
            if mkt_cap is not None:
                if mkt_cap < Config.MIN_MARKET_CAP:
                    reasons.append(f"Low Market Cap: ${mkt_cap:,.0f} < ${Config.MIN_MARKET_CAP:,.0f}")
            else:
                # If Market Cap is missing, we could optionally exclude it
                # For now, we allow it unless it's explicitly required
                pass
            
            # Volume (Turnover) Filter
            if turnover_24h < Config.MIN_VOLUME_24H:
                reasons.append(f"Low Turnover: ${turnover_24h:,.0f} < ${Config.MIN_VOLUME_24H:,.0f}")

            # OI Value Filter
            if oi_value < Config.MIN_OI_VALUE:
                reasons.append(f"Low OI Value: ${oi_value:,.0f} < ${Config.MIN_OI_VALUE:,.0f}")

            # Overextended Filter (Conditional)
            if Config.UNIVERSE_HARD_EXCLUDE_OVEREXTENDED and is_overextended:
                reasons.append("Asset is overextended (Hard Exclude enabled)")

            if not reasons:
                included.append(asset)
            else:
                asset_copy = asset.copy()
                asset_copy["exclusion_reasons"] = reasons
                excluded.append(asset_copy)

        logger.info(f"Universe Filter complete: {len(included)} included, {len(excluded)} excluded.")
        return included, excluded
