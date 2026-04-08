 document.addEventListener('DOMContentLoaded', function() {
    const input = document.querySelector('.search-input-wrapper input');                            
    const clearBtn = document.getElementById('clear-search');
                                                                                                    
    if (!input || !clearBtn) return;                                                                
                                                                                                    
    function toggleClear() {                                                                        
      clearBtn.style.display = input.value ? 'block' : 'none';                                      
    }                                                                                               
                                                                                                    
    input.addEventListener('input', toggleClear);
                                                                                                    
    clearBtn.addEventListener('click', () => {
      input.value = '';                   
      input.focus();                          
      clearBtn.style.display = 'none';                                                              
                                              
      const results = document.querySelector('.search-results');                                    
      if (results) results.innerHTML = '';                                                          
    });                                                                                             
                                                                                                    
    toggleClear();                                                                                  
  });