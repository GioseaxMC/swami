include { "stdlib.sw" }
include { "files.sw" }

func int main(int argc, ptr ptr char argv) {
  
  for(int i=1, i<argc, i++, {
    
    ptr char contents = read_file(argv[i], &size);
    
    printf("%s\n", contents);
  
  });
  
  return 0;
}

