"""
ETF 테이블 이미지 생성 모듈
"""
import logging
from typing import List, Dict
import pandas as pd
import matplotlib.pyplot as plt
from datetime import datetime
import io

logger = logging.getLogger(__name__)

# 한글 폰트 설정
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['axes.unicode_minus'] = False


class ETFTableGenerator:
    """ETF 데이터를 테이블 이미지로 변환하는 클래스"""
    
    @staticmethod
    def create_table_image(etf_data: List[Dict]) -> io.BytesIO:
        """
        ETF 데이터를 테이블 이미지로 생성
        
        Args:
            etf_data: ETF 정보 리스트
        
        Returns:
            이미지 바이트 스트림
        """
        try:
            # DataFrame 생성
            df_data = []
            for etf in etf_data:
                df_data.append({
                    'ETF': etf['symbol'],
                    'Current': f"${etf['current_price']:.2f}",
                    '52W Close': f"${etf['high_52w']:.2f}",
                    'High Date': etf['high_52w_date'],
                    'DD %': f"{etf['dd']:.2f}%",
                    'YTD %': f"{etf['ytd_return']:.2f}%",
                    'Daily %': f"{etf['daily_change']:+.2f}%",
                })
            
            df = pd.DataFrame(df_data)
            
            # 그림 생성
            fig, ax = plt.subplots(figsize=(14, 10))
            ax.axis('off')
            
            # 테이블 생성
            table = ax.table(
                cellText=df.values,
                colLabels=df.columns,
                cellLoc='center',
                loc='center',
                colWidths=[0.10, 0.12, 0.12, 0.12, 0.12, 0.12, 0.12]
            )
            
            # 스타일 설정
            table.auto_set_font_size(False)
            table.set_fontsize(9)
            table.scale(1, 2)
            
            # 헤더 스타일
            for i in range(len(df.columns)):
                table[(0, i)].set_facecolor('#4472C4')
                table[(0, i)].set_text_props(weight='bold', color='white')
            
            # 행 스타일 (교대로)
            for i in range(1, len(df) + 1):
                for j in range(len(df.columns)):
                    if i % 2 == 0:
                        table[(i, j)].set_facecolor('#E7E6E6')
                    else:
                        table[(i, j)].set_facecolor('#F2F2F2')
            
            # 제목 추가
            title = f"3X ETF LIST - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            plt.figtext(0.5, 0.98, title, ha='center', fontsize=14, weight='bold')
            
            # 이미지로 저장
            img_buffer = io.BytesIO()
            plt.tight_layout()
            plt.savefig(img_buffer, format='png', dpi=100, bbox_inches='tight')
            img_buffer.seek(0)
            plt.close()
            
            logger.info("ETF 테이블 이미지 생성 성공")
            return img_buffer
        
        except Exception as e:
            logger.error(f"테이블 이미지 생성 오류: {e}")
            return None
