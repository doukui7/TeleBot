"""Advanced ETF Table Generator"""
import logging
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class AdvancedETFTableGenerator:
    """Advanced ETF Table Generator"""
    
    @staticmethod
    def create_etf_message(etf_data: List[Dict]) -> str:
        """
        3X ETF 메시지 생성
        
        Args:
            etf_data: ETF 데이터 리스트
        
        Returns:
            포맷된 메시지 문자열
        """
        try:
            if not etf_data:
                return "No ETF data available"
            
            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d %H:%M:%S')
            
            message = f"<b>3X ETF List</b> - {date_str}\n"
            message += "<pre>\n"
            message += f"{'ETF':<7} {'Daily':>8}   {'Price':>14}   {'YTD':>8}   {'MTD':>8}   {'52W High':>14}   {'vs Low':>8}\n"
            message += "-" * 100 + "\n"
            
            for etf in etf_data:
                symbol = etf['symbol']
                daily = f"{etf['daily_change']:+.2f}%"
                price = f"$ {etf['current_price']:>12.2f}"
                ytd = f"{etf['ytd_return']:+.2f}%"
                mtd = f"{etf['monthly_return']:+.2f}%"
                high_52w = f"$ {etf['high_52w']:>12.2f}"
                vs_low = f"{etf['low_52w_change']:+.2f}%"
                
                message += f"{symbol:<7} {daily:>8}   {price:>14}   {ytd:>8}   {mtd:>8}   {high_52w:>14}   {vs_low:>8}\n"
            
            message += "</pre>"
            return message
        
        except Exception as e:
            return f"Error generating ETF message: {e}"
    
    @staticmethod
    def create_price_change_message(etf_data: List[Dict]) -> str:
        """
        ETF 가격 변동 메시지 생성 (상승/하락 랭킹)
        
        Args:
            etf_data: ETF 데이터 리스트
        
        Returns:
            포맷된 메시지 문자열
        """
        if not etf_data:
            return "ETF data is not available"
        
        now = datetime.now()
        date_str = now.strftime('%Y-%m-%d')
        
        message = f"<b>3X Leverage ETF Price Changes</b>\n"
        message += f"<b>{date_str} Close Prices</b>\n"
        message += "<pre>\n"
        
        gainers = [e for e in etf_data if e['daily_change'] >= 0]
        losers = [e for e in etf_data if e['daily_change'] < 0]
        
        gainers.sort(key=lambda x: x['daily_change'], reverse=True)
        losers.sort(key=lambda x: x['daily_change'])
        
        if gainers:
            message += "GAINERS\n"
            for etf in gainers[:15]:
                symbol = etf['symbol']
                price = etf['current_price']
                change = etf['daily_change']
                line = f"{symbol:5} ${price:>7.2f}  +{change:>5.2f}%"
                message += line + "\n"
        
        if gainers and losers:
            message += "\n"
        
        if losers:
            message += "LOSERS\n"
            for etf in losers[:15]:
                symbol = etf['symbol']
                price = etf['current_price']
                change = etf['daily_change']
                line = f"{symbol:5} ${price:>7.2f}  {change:>+6.2f}%"
                message += line + "\n"
        
        message += "</pre>"
        return message
