3
�� Z�B  �               @   s�  d dl mZmZ d dlmZmZmZmZmZm	Z	m
Z
mZmZmZmZmZmZmZ d dlZd dlZd dlZd dlZdadZdZddd	d
gae� adgd teg ag ae� ad ada da!dZ"dd� Z#dd� Z$dd� Z%dd� Z&dd� Z'dd� Z(dd� Z)dd� Z*dd � Z+G d!d"� d"�Z,G d#d$� d$�Z-d9d%d&�Z.d:d'd(�Z/d;d)d*�Z0e1d+k�r�e� a2et2�Z3ee3d,e.d-�Z4ee3d.e/d-�Z5ee3d/e0d0d1�Z6e4j7d2d3� e5j7d2d3� e6j7d2d3� e3j7d4d5d6� e,t2�Z8e8j9�  e-t2d4�Z:e-t2d7d8�Z;e*�  t2j<�  dS )<�    )�match�sub)�Tk�Text�	Scrollbar�Menu�
messagebox�
filedialog�
BooleanVar�Checkbutton�Label�Entry�	StringVar�Frame�Button�ENDNi�  i�  �   z^J[PNZ]?\s+.+z%^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGERz^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+z^[ASMDC]R?\s+[0-9]+\s*,\s*.+�   Fg      �?�3   c               C   s*   t � ad gd ttg ag at � adad S )Nr   r   )�dict�LABELS�MEMORY_START�PROGRAM_START�REGISTER�MEMORY�MEMORY_LABELS�STATE� r   r   �interpreter.py�reset_state   s
    r   c              C   s�   da x~t d7 a tj� } tj� j� }tdd|�}td|�r:qd}xtD ]}t||�rDd}P qDW |rt| t ft|j	� d < td	|�rP qW d S )
Ng        g      �?z\#.*� z^\s*$TFr   z^\s*KONIEC\s*$)
�CURRENT_LINE�program�tell�readline�lstripr   r   �ORDERSr   �split)�location�lineZis_label�regexr   r   r   �preprocess_labels   s"    
 

 
 r+   c             C   sJ   t t| � dkrdan0t t| � dkr,dant t| � dk rBdandad S )Nr   �   �   �   )r   �intr   )�targetr   r   r   �	set_state1   s       r1   c             C   s�   t d| �rt|  t t S t d| �r4t| �t t S t d| �r|tdd| �jd�} t| d �}t| d �}ttt	| | ��S d S )	Nz	^[A-Z_]+$z^[0-9]+$z^\-?[0-9]+\([0-9]+\)$z\)r    �(r   r,   )
r   r   r   �WORD_LENGTHr/   r   r'   �get_short_adress�strr   )�labelZdelta�registerr   r   r   r4   8   s    
 
 
r4   c             C   s   t t�t t t| < d S )N)�lenr   r3   r   r   )r6   r   r   r   �store_labelA   s    r9   c             C   s&   x t j� D ]\}}|| kr
|S q
W dS )Nr    )r   �items)Zinput_adressr6   Zadressr   r   r   �	get_labelE   s     r;   c             C   s�  t d| �rd S d}| j� j� } xtD ]}t || �r$d}P q$W |r`| j� } | jd� dj| �j� } t d| ��r�t d| �r�tdd| �j� } | d }| d	 }|d
kr�t| d �}t	|� t
j|� n|dkr�t	|� t
jd � n�t d| ��r�tddtdd| ��j� } | d jd�| d< | d }| d	 }t| d d �}|d
k�rrt| d d	 �}t	|� xNt|�D ]}t
j|� �q\W n0|dk�r�t	|� xt|�D ]}t
jd � �q�W �n�t d| ��rdtddtdd| ��j� } | d }| d	 }	t| d �}
|dk�rt
|
 tt|	�< n^|dk�r"|
t t tt|	�< n>|dk�rFtt| d � tt|	�< n|dk�r�tt|	� t
|
< �n2t d| ��r�tddtdd| ��j� } | d }| d	 }	| d }
t d|��r�tt|
� }
nt
t| d � }
t d|��r�tt|	�  |
7  < ndt d|��rtt|	�  |
8  < nBt d|��r0tt|	�  |
9  < n t d|��rPtt|	�  |
  < t|	� t d |��r�tt|	� }	|	|
k�r�dan$|	|
k�r�d	an|	|
k �r�dandan�t d!| ��r�| j� } | d }tdd| d	 �}|d"k�r�tjt| d � t| d	 an�|d#k�r0td	k�r�tjt| d � t| d	 anf|d$k�rdtdk�r�tjt| d � t| d	 an2|d%k�r�tdk�r�tjt| d � t| d	 ad S )&Nz^\s*$TFr   � z%^[A-Z_]+\s+D[CS]\s+([0-9]+\*)?INTEGERz^[A-Z_]+\s+D[CS]\s+INTEGERz[\(\)
]r,   ZDCr.   ZDSz"^[A-Z_]+\s+D[CS]\s+[0-9]+\*INTEGERz[\)
]r    z\s*\(r-   z*INTEGERz^(L[AR]?|ST)\s+[0-9]+\s*,\s*.+�,�
�LZLAZLRZSTz^[ASMDC]R?\s+[0-9]+\s*,\s*.+z.Rz^Az^Sz^Mz^Dz^Cz^J[PNZ]?\s+[A-Z_]+�JZJPZJNZJZ)r   r%   �rstripr&   r'   �pop�joinr   r/   r9   r   �append�ranger4   r   r3   r   r1   r   r"   �seekr   r!   )r)   Z	has_labelr*   r6   �order�value�countZnumber�_r0   �sourcer   r   r   �	interpretJ   s�    
 




 
 
 
 
 
      
 
 
 






rL   c              C   s�   t t�jd�d } tdk r"d|  } d|  d }xDttt��D ]4}|t|� d tt| � d tt| � d }q<W tj	|� d	}x`ttt
��D ]P}|t|t t � d tt
| � d t|t t � d tt
| � d }q�W tj	|� d S )
N�br,   r-   �0zSTATE:	z)
REGISTERS:
INDEX	VALUE	TWO'S COMPLEMENT
�	r>   z/MEMORY:
ADRESS	VALUE:	LABEL:	TWO'S COMPLEMENT:
)�binr   r'   rE   r8   r   r5   �	int_to_u2�	registers�print_outputr   r3   r   r;   �memory)Zformated_stateZregisters_text�xZmemory_textr   r   r   �dump_all�   s     4
PrV   c             C   s\   | d krdS t | dtd >  �jd�d }| dkrXx$tdt t|� �D ]}d| }qHW |S )Nr    r,   �   rM   r   rN   )rP   r3   r'   rE   r8   )ZintegerZbinary�ir   r   r   rQ   �   s      rQ   c               @   sx   e Zd Zdd� Zddd�Zddd�Zddd	�Zdd
d�Zddd�Zddd�Z	ddd�Z
ddd�Zd dd�Zd!dd�ZdS )"�Editorc             C   sN  || _ d| _d | _| j�  t|�}t|dd�| _t|dd�| _t|| jj	| jj	ddd�| _
| j
jdd	d
d� | j
jddtd� | j
j�  |jdddd� |jd| j� t|�| _t| jdd�}|jdd
| jdd� |jdd
| jdd� |jdd
| jdd� |jdd| jdd� |j�  |jdd| jd d� | jjd!d|d"� |j| jd#� d S )$NzPseudoassembler IDE�vertical)�orient�
horizontal�whiteZxterm)�yscrollcommand�xscrollcommandZbg�cursor�top�yr,   )�side�fill�expand�noneT)�wrap�undo�width�leftZbothr   ZWM_DELETE_WINDOW)ZtearoffZNewzCtrl+N)r6   �	underline�commandZacceleratorzOpen...zCtrl+OZSavezCtrl+Sz
Save As...�   z
Ctrl+Alt+SZExitr-   zAlt+F4ZFile)r6   rk   �menu)rn   )�root�TITLE�	file_path�	set_titler   r   Z
yscrollbarZ
xscrollbarr   �set�editor�pack�config�EDITOR_WIDTHZfocusZprotocol�	file_quitr   ZmenubarZadd_command�file_new�	file_open�	file_save�file_save_asZadd_separatorZadd_cascade)�selfro   �frameZfilemenur   r   r   �__init__�   s2    

zEditor.__init__Nc             C   sB   | j j� r:tjdd�}|r4| j� }|dkr.dS d S q>|S ndS d S )NzSave?z=This document has been modified. Do you want to save changes?�savedT)rt   �edit_modifiedr   Zaskyesnocancelr{   )r}   �eventZresponse�resultr   r   r   �save_if_modified�   s    
zEditor.save_if_modifiedc             C   sF   | j � }|d krB| jjdd� | jjd� | jj�  d | _| j�  d S )Ng      �?�endF)r�   rt   �deleter�   Z
edit_resetrq   rr   )r}   r�   r�   r   r   r   ry   �   s    
zEditor.file_newc          
   C   s�   | j � }|d kr�|d kr tj� }|d kr�|dkr�t|dd��}|j� }W d Q R X | jjdd� | jjd|� | jjd� || _	| j
�  d S )Nr    zutf-8)�encodingg      �?r�   F)r�   r	   Zaskopenfilename�open�readrt   r�   �insertr�   rq   rr   )r}   r�   �filepathr�   �fZfileContentsr   r   r   rz   �   s    zEditor.file_openc             C   s&   | j d kr| j� }n| j| j d�}|S )N)r�   )rq   r|   )r}   r�   r�   r   r   r   r{     s    

zEditor.file_savec             C   s�   |d krt jdd�}yRt|d��>}| jjd	d
�}|jt|d�� | jjd� || _| j	�  dS Q R X W n t
k
r�   td� dS X d S )N�
Text files�*.txt�Python files�
*.py *.pyw�	All files�*.*)Z	filetypes�wbg      �?zend-1czUTF-8Fr�   �FileNotFoundErrorZ	cancelled�r�   r�   �r�   r�   �r�   r�   )r�   r�   r�   )r	   Zasksaveasfilenamer�   rt   �get�write�bytesr�   rq   rr   r�   �print)r}   r�   r�   r�   �textr   r   r   r|   
  s    zEditor.file_save_asc             C   s   | j � }|d kr| jj�  d S )N)r�   ro   Zdestroy)r}   r�   r�   r   r   r   rx     s    zEditor.file_quitc             C   s8   | j d krtjj| j �}nd}| jj|d | j � d S )NZUntitledz - )rq   �os�path�basenamero   �titlerp   )r}   r�   r�   r   r   r   rr     s    
zEditor.set_titlec             C   s   | j j�  d S )N)rt   Z	edit_undo)r}   r�   r   r   r   rh   %  s    zEditor.undoc             C   s   | j j�  d S )N)rt   Z	edit_redo)r}   r�   r   r   r   �redo(  s    zEditor.redoc             C   s�   | j jd| j� | j jd| j� | j jd| j� | j jd| j� | j jd| j� | j jd| j� | j jd| j� | j jd| j� | j jd	t� d S )
Nz<Command-o>z<Command-O>z<Command-S>z<Command-s>z<Command-y>z<Command-Y>z<Command-Z>z<Command-z>z<Command-b>)rt   Zbindrz   r{   r�   rh   �run_code)r}   r�   r   r   r   �main+  s    zEditor.main)N)N)NN)N)NN)N)N)N)N)N)�__name__�
__module__�__qualname__r   r�   ry   rz   r{   r|   rx   rr   rh   r�   r�   r   r   r   r   rY   �   s   "

	






rY   c               @   s   e Zd Zddd�Zdd� ZdS )�Output�   c             C   sl   || _ t| j dd�| _t| j dd�| _t| j |d| jj| jjdd�| _| jjddd	� | jj|d
dd� d S )NrZ   )r[   r\   �<   Zarrow)�heightri   r^   r_   r`   �disabledrf   )�staterg   rU   r,   )rc   rd   re   )	ro   r   ZyscrollZxscrollr   rs   �fieldrv   ru   )r}   ro   rc   r�   r   r   r   r   7  s     zOutput.__init__c             C   s<   | j jdd� | j jdt� | j jd|� | j jdd� d S )N�normal)r�   z1.0r�   )r�   rv   r�   r   r�   )r}   r�   r   r   r   rS   >  s    zOutput.print_outputN)r�   )r�   r�   r�   r   rS   r   r   r   r   r�   6  s   
r�   c             C   sx   t j�  tt jdd�at�  t�  tjd� x8tj� }t	dd|�}t
d|�rNq.t
d|�rZP t|� q.W t�  tj�  d S )N�r)�moder   z\#.+r    z^\s*$z^\s*KONIEC\s*$)rt   r�   r�   rq   r"   r   r+   rF   r$   r   r   rL   rV   �close)r�   r)   r   r   r   r�   D  s    

 
 r�   c             C   s�   t sdda tjdd� tjdd� tjdd� tj�  ttjdd�a	t
�  t�  t	jd	� d
at�  nBda d
atjdd� tjdd� tjdd� t
�  tjjddt� d S )NTzEXIT BY LINE MODE)r�   r�   )r�   r�   r�   )r�   r   g      �?FzRUN BY LINE�current_linez1.0)�BY_LINE_MODE�run_by_line_buttonrv   �next_line_button�
run_buttonrt   r�   r�   rq   r"   r   r+   rF   r!   �	next_line�
tag_remover   )r�   r   r   r   �run_by_lineW  s&    
r�   c             C   s�   t j jdtt�tttd  �� t j jdddd� t j jddtt�� t j jdtttd  �t� td7 atj	� }t
dd	|�}td
|�r�t�  d S t|� t�  d S )Nr�   �d   Zblackr]   )Z
backgroundZ
foregroundz1.0g      �?z\#.+r    z^\s*KONIEC\s*$)rt   Ztag_addr5   r!   rw   Z
tag_configr�   r   r"   r$   r   r   r�   rL   rV   )r�   r)   r   r   r   r�   p  s     
r�   �__main__zRUN CODE)r�   rl   zRUN BY LINEz	NEXT LINEr�   )r�   rl   r�   rj   )rc   ra   rU   )rc   rd   Zbottomr�   )N)N)N)=�rer   r   Ztkinterr   r   r   r   r   r	   r
   r   r   r   r   r   r   r   r�   �
subprocessZjson�stringr   r   r3   r&   r   r   r   r   r   r   r�   r!   rw   r   r+   r1   r4   r9   r;   rL   rV   rQ   rY   r�   r�   r�   r�   r�   ro   Zbuttonsr�   r�   r�   ru   rt   r�   rR   rT   Zmainloopr   r   r   r   �<module>   sX   @ 	[|




